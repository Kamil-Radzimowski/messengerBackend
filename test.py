import connexion
import pytest
import json
import databaseConnect

test_id = None
friend_id = None
api_key = None
friend_api_key = None
invalid_key = "none"

test_name = "Kamil"
test_surname = "R"
test_email = "example@com.pl"
wrong_email = "null@null.com"
test_password = "password"
wrong_password = "word"
test_phone = 999666333
wrong_phone = 555444333

friends_name = "Friend"
friends_surname = "Surname"
friends_email = "imafriend@com.pl"
friends_password = "imapassword"
friends_phone = 999888777

relation_id = None
conversation_id = None

message = "test_message"
long_message = "Z0mygGA06FfNpsg2IrMnKpbiN1JsHSRTfXgE18B2GDiRu2eGtyeBLqZaxjrEPxU2vcgtPSu4Ob5Bgn80aD8ozT2A3jkpUgGVDaJm" \
               "RgkaiA6SRaTzaZ76LuHSaEXKsuc5pHEsvATrRaFxkXgcnBr28OYqap2V3fZ08lVl24hxKbQ2ut11TX56XilaVT77wkRZucb6yhmX" \
               "RjjfpNeGIvSp2bfpdKTQ96HaSquYg8tfwibn4d6D9NfLRlZJ16Qmr35xxJkKQ3Pmds636kye5gK7KX5klJ9wTKbjyRKD8c8o8sIS" \
               "M4dNJTAAfQSTdn0EQfb9zQyzEwCaniTeGoiDqaLtHN2UutISw6BZYRJncDRx2MzQTU3tuvg2KdgfLcCsWH5WkFf2LnPNkbApLZnp "


@pytest.fixture
def app():
    app = connexion.App(__name__, specification_dir='.')
    app.add_api('messengerSwagger.yml')
    return app.app.test_client()


def test_api(app):
    request = app.get(f"api/my")
    assert request.status_code == 404


def test_user_create(app):
    # Create main account
    response = app.put(
        f"api/createUser?"
        f"email={test_email}&&"
        f"phoneNumber={test_phone}&&"
        f"password={test_password}&&"
        f"name={test_name}&&"
        f"surname={test_surname}")
    assert response.status_code == 200

    # Create friend's account
    response_2 = app.put(
        f"api/createUser?"
        f"email={friends_email}&&"
        f"phoneNumber={friends_phone}&&"
        f"password={friends_password}&&"
        f"name={friends_name}&&"
        f"surname={friends_surname}"
    )
    assert response_2.status_code == 200


def test_user_create_check_database(app):
    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = "SELECT name FROM messenger_users WHERE surname IN (%s, %s)"
    cursor.execute(query, (test_surname, friends_surname,))
    result = cursor.fetchall()
    assert result[0][0] == test_name
    assert result[1][0] == friends_name


def test_user_already_exists_same_email(app):
    second_response = app.put(f"api/createUser?"
                              f"email={test_email}&&"
                              f"phoneNumber={wrong_phone}&&"
                              f"password={test_password}&&"
                              f"name={test_name}&&"
                              f"surname={test_surname}")
    assert second_response.status_code == 409
    assert second_response.get_data(as_text=True) == "User already exists"

    # Check if there isn't an extra entry in the database
    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = "SELECT name FROM messenger_users WHERE surname IN (%s, %s)"
    cursor.execute(query, (test_surname, friends_surname))
    result = cursor.fetchall()
    assert len(result) == 2


def test_user_already_exists_same_phone(app):
    second_response = app.put(f"api/createUser?"
                              f"email={wrong_email}&&"
                              f"phoneNumber={test_phone}&&"
                              f"password={test_password}&&"
                              f"name={test_name}&&"
                              f"surname={test_surname}")
    assert second_response.status_code == 409
    assert second_response.get_data(as_text=True) == "User already exists"

    # Check if there isn't an extra entry in the database
    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = "SELECT name FROM messenger_users WHERE surname IN (%s, %s)"
    cursor.execute(query, (test_surname, friends_surname))
    result = cursor.fetchall()
    assert len(result) == 2


def test_login_user_using_email(app):
    successful_login = app.get(f"api/loginUser?email={test_email}&&password={test_password}")
    assert successful_login.status_code == 200
    assert "api_key" in successful_login.get_data(as_text=True)
    assert "id" in successful_login.get_data(as_text=True)


def test_login_user_using_phone(app):
    global test_id, api_key, friend_id, friend_api_key
    successful_login = app.get(f"api/loginUser?phoneNumber={test_phone}&&password={test_password}")
    assert successful_login.status_code == 200
    assert "api_key" in successful_login.get_data(as_text=True)
    assert "id" in successful_login.get_data(as_text=True)

    data = json.loads(successful_login.get_data(as_text=True))
    test_id = data["id"]
    api_key = data["api_key"]

    friends_login = app.get(f"api/loginUser?phoneNumber={friends_phone}&&password={friends_password}")
    assert friends_login.status_code == 200
    friends_data = json.loads(friends_login.get_data(as_text=True))
    friend_id = friends_data["id"]
    friend_api_key = friends_data["api_key"]


def test_load_users_by_string(app):
    response = app.get(f"api/loadUsersByString?userId={test_id}&&apiKey={api_key}&&givenString={friends_name}")
    assert response.status_code == 200
    data = json.loads(response.get_data(as_text=True))
    assert data["users"][0]["id"] == friend_id
    assert len(data["users"]) == 1


def test_load_users_by_string_invalid_id(app):
    response = app.get(f"api/loadUsersByString?userId={0}&&apiKey={api_key}&&givenString={friends_name}")
    assert response.status_code == 401


def test_load_users_by_string_invalid_api_key(app):
    response = app.get(f"api/loadUsersByString?userId={test_id}&&apiKey={invalid_key}&&givenString={friends_name}")
    assert response.status_code == 401


def test_load_users_by_string_search_for_yourself(app):
    response = app.get(f"api/loadUsersByString?userId={friend_id}&&apiKey={friend_api_key}&&givenString={friends_name}")
    assert response.status_code == 200
    data = json.loads(response.get_data(as_text=True))
    assert len(data["users"]) == 0


def test_login_user_wrong_email(app):
    failed_login = app.get(f"api/loginUser?email={wrong_email}&&password={wrong_password}")
    assert failed_login.status_code == 400
    assert failed_login.get_data(as_text=True) == "Invalid email or phone number"


def test_login_user_wrong_phone(app):
    failed_login = app.get(f"api/loginUser?phoneNumber={wrong_phone}&&password={wrong_password}")
    assert failed_login.status_code == 400
    assert failed_login.get_data(as_text=True) == "Invalid email or phone number"


def test_add_friend(app):
    request = app.put(f"api/sendFriendRequest?userId={test_id}&&friendsId={friend_id}&&apiKey={api_key}")
    assert request.status_code == 200

    # Check the database for the request
    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = f"SELECT * FROM messenger_friends WHERE user_id = {test_id}"
    cursor.execute(query)
    record = cursor.fetchall()
    assert record[0][2] == friend_id
    assert record[0][1] == test_id
    assert not record[0][3]


def test_load_friend_requests(app):
    global relation_id
    result = app.get(f"api/loadFriendRequests?userId={friend_id}&&apiKey={friend_api_key}")
    assert result.status_code == 200
    result_json = json.loads(result.get_data(as_text=True))
    assert isinstance(result_json["requests"][0]["relation_id"], int)
    relation_id = result_json["requests"][0]["relation_id"]
    assert result_json["requests"][0]["name"] == "Kamil R"


def test_load_number_of_friend_requests(app):
    result = app.get(f"api/loadNumberOfFriendRequests?userId={friend_id}&&apiKey={friend_api_key}")
    assert result.status_code == 200
    number_of_requests = json.loads(result.get_data(as_text=True))
    assert number_of_requests["result"][0] == 1


def test_load_number_of_friend_requests_invalid_id(app):
    result = app.get(f"api/loadNumberOfFriendRequests?userId={0}&&apiKey={friend_api_key}")
    assert result.status_code == 401


def test_load_number_of_friend_requests_invalid_api_key(app):
    result = app.get(f"api/loadNumberOfFriendRequests?userId={friend_id}&&apiKey={invalid_key}")
    assert result.status_code == 401


def test_decline_friend_request(app):
    global relation_id
    request = app.put(f"api/answerFriendRequest?"
                      f"userId={friend_id}&&"
                      f"apiKey={friend_api_key}&&"
                      f"requestId={relation_id}&&"
                      f"isAccepted={False}")
    assert request.status_code == 200

    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = f"SELECT * FROM messenger_friends WHERE user_id = {test_id}"
    cursor.execute(query)
    record = cursor.fetchall()
    assert len(record) == 0

    send_second_request = app.put(f"api/sendFriendRequest?userId={test_id}&&friendsId={friend_id}&&apiKey={api_key}")
    assert send_second_request.status_code == 200

    # Check the database for the request
    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = f"SELECT * FROM messenger_friends WHERE user_id = {test_id}"
    cursor.execute(query)
    record = cursor.fetchall()
    assert record[0][2] == friend_id
    assert record[0][1] == test_id
    assert not record[0][3]

    result = app.get(f"api/loadFriendRequests?userId={friend_id}&&apiKey={friend_api_key}")
    assert result.status_code == 200
    result_json = json.loads(result.get_data(as_text=True))
    assert isinstance(result_json["requests"][0]["relation_id"], int)
    relation_id = result_json["requests"][0]["relation_id"]
    assert result_json["requests"][0]["name"] == "Kamil R"


def test_confirm_friend_request(app):
    request = app.put(f"api/answerFriendRequest?"
                      f"userId={friend_id}&&"
                      f"requestId={relation_id}&&"
                      f"apiKey={friend_api_key}&&"
                      f"isAccepted={True}")
    assert request.status_code == 200

    # Check the database for the request
    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = f"SELECT * FROM messenger_friends WHERE user_id = {test_id}"
    cursor.execute(query)
    record = cursor.fetchall()
    assert record[0][2] == friend_id
    assert record[0][1] == test_id
    assert record[0][3]


def test_add_friend_invalid_friends_id(app):
    request = app.put(f"api/sendFriendRequest?userId={test_id}&&friendsId={0}&&apiKey={api_key}")
    assert request.status_code == 409


def test_add_friend_invalid_api_key(app):
    request = app.put(f"api/sendFriendRequest?userId={test_id}&&friendsId={0}&&apiKey={invalid_key}")
    assert request.status_code == 401


def test_login_user_wrong_password(app):
    failed_login = app.get(f"api/loginUser?email={test_email}&&password={wrong_password}")
    assert failed_login.status_code == 400
    assert failed_login.get_data(as_text=True) == "Wrong password"


def test_load_data(app):
    global conversation_id
    request = app.get(f"api/loadData?userId={test_id}&&apiKey={api_key}")
    assert request.status_code == 200

    result = json.loads(request.get_data(as_text=True))
    assert len(result["conversations"]) == 1

    conversation_id = result["conversations"][0]["id"]
    assert result["conversations"][0]["last_message"] is None
    assert len(result["conversations"][0]["users"]) == 2


def test_send_message(app):
    request = app.put(f"api/sendMessage?"
                      f"userId={test_id}&&"
                      f"conversationId={conversation_id}&&"
                      f"message={message}&&"
                      f"apiKey={api_key}")
    assert request.get_data(as_text=True) == "Message sent successfully"
    assert request.status_code == 200

    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = f"SELECT message FROM messenger_messages WHERE authors_id = {test_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    connect.close()
    assert result[0] == message


def test_send_message_invalid_api_key(app):
    failed_request = app.put(f"api/sendMessage?"
                             f"userId={test_id}&&"
                             f"conversationId={conversation_id}&&"
                             f"message={message}&&"
                             f"apiKey={invalid_key}")
    assert failed_request.status_code == 401


def test_send_message_invalid_friend_id(app):
    failed_request = app.put(f"api/sendMessage?"
                             f"userId={test_id}&&"
                             f"conversationId={0}&&"
                             f"message={message}&&"
                             f"apiKey={api_key}")
    assert failed_request.status_code == 406


def test_send_message_very_long_text(app):
    request = app.put(f"api/sendMessage?"
                      f"userId={test_id}&&"
                      f"conversationId={conversation_id}&&"
                      f"message={long_message}&&"
                      f"apiKey={api_key}")
    assert request.status_code == 200

    # Check if there is an extra entry in the database
    connect = databaseConnect.get_connection()
    cursor = connect.cursor()
    query = "SELECT * FROM messenger_messages"
    cursor.execute(query)
    result = cursor.fetchall()
    assert len(result) == 2


def test_load_data_wrong_id(app):
    request = app.get(f"api/loadData?userId={0}&&apiKey={api_key}")
    assert request.status_code == 401


def test_load_data_wrong_api_key(app):
    request = app.get(f"api/loadData?userId={test_id}&&apiKey={invalid_key}")
    assert request.status_code == 401


def test_load_conversation(app):
    request = app.get(f"api/loadConversation?userId={test_id}&&apiKey={api_key}&&conversationId={conversation_id}")
    assert request.status_code == 200

    result = json.loads(request.get_data(as_text=True))
    assert result["conversation"][0]["message"] == message
    assert result["conversation"][1]["message"] == long_message


def test_load_conversation_friends_perspective(app):
    request = app.get(f"api/loadConversation?"
                      f"userId={friend_id}&&"
                      f"apiKey={friend_api_key}&&"
                      f"conversationId={conversation_id}")
    assert request.status_code == 200

    result = json.loads(request.get_data(as_text=True))
    assert result["conversation"][0]["message"] == message
    assert result["conversation"][1]["message"] == long_message


def test_delete_user(app):
    # Delete user and friend instance after the test
    connection = databaseConnect.get_connection()
    cursor = connection.cursor()
    query_messages = f"DELETE FROM messenger_messages WHERE authors_id = {test_id}"
    cursor.execute(query_messages)
    query_conversation_users = f"DELETE FROM conversation_users WHERE conversation_id = {conversation_id}"
    cursor.execute(query_conversation_users)
    query_conversation = f"DELETE FROM messenger_conversations WHERE conversation_id = {conversation_id}"
    cursor.execute(query_conversation)
    query_friends = f"DELETE FROM messenger_friends WHERE user_id = {test_id} or friend_id = {test_id}"
    cursor.execute(query_friends)
    query_users = "DELETE FROM messenger_users WHERE email = %s or email = %s"
    cursor.execute(query_users, (test_email, friends_email,))
    connection.commit()
    connection.close()
    cursor.close()

