import os
import requests

class PredictionService:
    def __init__(self):
        self.pfe_base_url = os.environ.get('PFE_API_URL', 'http://localhost:8000')

    def predict_image(self, file_url_or_path):
        try:
            if file_url_or_path.startswith('http'):
                image_response = requests.get(file_url_or_path)
                image_response.raise_for_status()
                if not image_response.content:
                    raise Exception("Downloaded image from URL is empty")
                files = {'file': ('image.jpg', image_response.content, 'image/jpeg')}
            else:
                files = {'file': open(file_url_or_path, 'rb')}
            
            response = requests.post(f"{self.pfe_base_url}/predict/image", files=files)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to communicate with PFE model: {str(e)}")

    def predict_symptoms(self, symptoms_text):
        try:
            payload = {"description": symptoms_text}
            response = requests.post(f"{self.pfe_base_url}/predict/symptoms", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to communicate with PFE model: {str(e)}")

    def predict_fused(self, file_url_or_path, symptoms_text):
        try:
            if file_url_or_path.startswith('http'):
                image_response = requests.get(file_url_or_path, headers={'User-Agent': 'Mozilla/5.0'})
                image_response.raise_for_status()
                if not image_response.content:
                    raise Exception("Downloaded image from URL is empty")
                files = {'file': ('image.jpg', image_response.content, 'image/jpeg')}
            else:
                files = {'file': open(file_url_or_path, 'rb')}
            
            data = {"description": symptoms_text}
            response = requests.post(f"{self.pfe_base_url}/predict/fused", files=files, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to communicate with PFE model: {str(e)}")
