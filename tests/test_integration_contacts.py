from datetime import date


test_contact = {
    "first_name": "name",
    "last_name": "surname",
    "email": "test@ukr.net",
    "phone": "7017012222",
    "birth_date": str(date(2001, 12, 12)),
}


def test_create_contact(client, get_token):
    """
    Тестує створення нового контакту через POST-запит.
    Перевіряє статус-код відповіді, а також наявність імені, телефону та ID в тілі відповіді.
    """
    response = client.post(
        "/api/contacts",
        json=test_contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == test_contact["first_name"]
    assert "id" in data
    assert "phone" in data


def test_get_contact(client, get_token):
    """
    Тестує отримання контакту за ID.
    Перевіряє статус-код 200 та правильність отриманих даних (ім'я та ID).
    """
    response = client.get(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == test_contact["first_name"]
    assert "id" in data


def test_get_contact_not_found(client, get_token):
    """
    Тестує спробу отримати неіснуючий контакт.
    Очікується статус-код 404 та повідомлення про те, що контакт не знайдено.
    """
    response = client.get(
        "/api/contacts/7", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Контакт не знайдено"


def test_get_contacts(client, get_token):
    """
    Тестує отримання списку всіх контактів.
    Перевіряє, що відповідь має статус 200, є списком, та що щонайменше один елемент має правильне ім’я та ID.
    """
    response = client.get(
        "/api/contacts", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == test_contact["first_name"]
    assert "id" in data[0]
    assert len(data) > 0


def test_update_contact(client, get_token):
    """
    Тестує оновлення існуючого контакту (PUT-запит).
    Змінює ім’я та перевіряє, що відповідь містить оновлене значення і правильний ID.
    """
    updated_test_contact = test_contact.copy()
    updated_test_contact["first_name"] = "New_first_name"

    response = client.put(
        "/api/contacts/1",
        json=updated_test_contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["first_name"] == "New_first_name"
    assert "id" in data
    assert data["id"] == 1


def test_update_contact_not_found(client, get_token):
    """
    Тестує спробу оновити неіснуючий контакт (PATCH-запит).
    Очікується статус-код 404 та повідомлення "Not Found".
    """
    updated_test_contact = test_contact.copy()
    updated_test_contact["first_name"] = "New_first_name"

    response = client.patch(
        "/api/contact/2",
        json=updated_test_contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Not Found"


def test_delete_contact(client, get_token):
    """
    Тестує видалення існуючого контакту.
    Перевіряє, що повертається правильний ID та ім’я видаленого контакту.
    """
    response = client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    data = response.json()
    assert data["id"] == 1
    assert data["first_name"] == "New_first_name"


def test_repeat_delete_contact(client, get_token):
    """
    Тестує повторне видалення вже видаленого контакту.
    Очікується статус-код 404 та повідомлення "Контакт не знайдено".
    """
    response = client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Контакт не знайдено"
