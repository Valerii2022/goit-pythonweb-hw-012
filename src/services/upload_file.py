import cloudinary
import cloudinary.uploader

class UploadFileService:
    """
    Клас для взаємодії з Cloudinary API для завантаження файлів.

    Цей клас забезпечує налаштування для підключення до Cloudinary та завантаження файлів,
    а також створення публічних URL для завантажених зображень.
    """

    def __init__(self, cloud_name, api_key, api_secret):
        """
        Ініціалізує сервіс для завантаження файлів на Cloudinary.

        Args:
            cloud_name (str): Ім'я хмари в Cloudinary.
            api_key (str): API ключ для доступу до Cloudinary.
            api_secret (str): API секрет для доступу до Cloudinary.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """
        Завантажує файл на Cloudinary і повертає URL для доступу до зображення.

        Створюється унікальний `public_id` для кожного користувача на основі його імені.

        Args:
            file: Файл, який потрібно завантажити.
            username (str): Ім'я користувача, яке використовується для формування публічного ID.

        Returns:
            str: URL для доступу до завантаженого зображення.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
