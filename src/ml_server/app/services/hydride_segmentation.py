import requests

from ...config import Config


class HydrideSegmentationService:
    """Service wrapper for the hydride segmentation model."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.settings = self.config.hydride_segmentation_settings

    @property
    def model_url(self) -> str:
        return self.settings.get("ml_model", {}).get("url", "")

    @property
    def health_url(self) -> str:
        return self.settings.get("ml_model", {}).get("health_url", "")

    def is_available(self) -> bool:
        try:
            resp = requests.get(self.health_url, timeout=3)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def segment(self, image_file) -> bytes:
        """Send image data to the segmentation model and return the segmented image."""
        files = {"image": image_file}
        response = requests.post(
            self.model_url,
            files=files,
            timeout=self.settings.get("ml_model", {}).get("timeout", 30),
        )
        if response.status_code != 200:
            raise RuntimeError("Model processing failed")
        return response.content
