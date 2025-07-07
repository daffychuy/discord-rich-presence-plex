from app import config, logger
from PIL import Image, ImageOps
from typing import Optional, TypedDict
import io
import requests

class UploadResponseData(TypedDict):
	error: str
	link: str

class UploadResponse(TypedDict):
	success: bool
	status: int
	data: UploadResponseData

def upload(url: str) -> Optional[str]:
	try:
		originalImageBytesIO = io.BytesIO(requests.get(url).content)
		originalImage = Image.open(originalImageBytesIO).convert("RGBA")
		newImage = Image.new("RGBA", originalImage.size)
		newImage.putdata(originalImage.getdata()) # pyright: ignore[reportUnknownArgumentType,reportUnknownMemberType]
		if newImage.width != newImage.height and config.config["display"]["posters"]["fit"]:
			longestSideLength = max(newImage.width, newImage.height)
			newImage = ImageOps.pad(newImage, (longestSideLength, longestSideLength), color = (0, 0, 0, 0))
		maxSize = config.config["display"]["posters"]["maxSize"]
		if maxSize:
			newImage.thumbnail((maxSize, maxSize))
		newImageBytesIO = io.BytesIO()
		newImage.save(newImageBytesIO, subsampling = 0, quality = 90, format = "PNG")
		response = requests.post(
			"https://api.imgur.com/3/image",
			headers = { "Authorization": f"Client-ID {config.config['display']['posters']['imgurClientID']}" },
			files = { "image": newImageBytesIO.getvalue() }
		)
		logger.debug("HTTP %d, %s, %s", response.status_code, response.headers, response.text.strip())
		data: UploadResponse = response.json()
		if not data["success"]:
			raise Exception(data["data"]["error"])
		return data["data"]["link"]
	except:
		logger.exception("An unexpected error occured while uploading an image to Imgur")
