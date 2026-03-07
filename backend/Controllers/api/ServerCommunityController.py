from flask import jsonify, request, session

from backend.Repositories.ServerChannelRepository import ServerChannelRepository
from backend.Repositories.ServerFileRepository import ServerFileRepository
from backend.Repositories.ServerMessageRepository import ServerMessageRepository
from backend.Repositories.ServerUserRepository import ServerUserRepository
from backend.Services.ServerCommunityService import ServerCommunityService
from backend.configurations import SortOrder, SortOrderStr


server_community_service = ServerCommunityService(
    user_repository=ServerUserRepository(),
    channel_repository=ServerChannelRepository(),
    message_repository=ServerMessageRepository(),
    file_repository=ServerFileRepository(),
)


def _parse_int_arg(value, default_value: int, min_value: int = 1, max_value: int = 500):
    try:
        parsed = int(value)
    except Exception:
        parsed = default_value
    return max(min_value, min(parsed, max_value))


def _parse_bool_arg(value, default_value: bool = False):
    if value is None:
        return bool(default_value)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _get_server_user_doc():
    user_id = str(session.get("server_user_id") or "").strip()
    if not user_id:
        return None
    server_community_service.touch_user_activity(user_id)
    return server_community_service.get_user_document_by_id(user_id)


def server_me_route():
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401
    return jsonify({"user": server_community_service.serialize_user(user)})


def server_channels_route():
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    if request.method == "GET":
        rows = server_community_service.list_channels_for_user(user)
        return jsonify({"channels": rows})

    payload = request.get_json(silent=True) or request.form
    try:
        created = server_community_service.create_channel(
            user_document=user,
            data={
                "name": payload.get("name"),
                "description": payload.get("description"),
                "channel_type": payload.get("channel_type"),
                "is_public": payload.get("is_public", True),
            },
        )
        return jsonify({"message": "Channel created.", "channel": created}), 201
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_channel_detail_route(channel_id):
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form
    try:
        if request.method == "PUT":
            updated = server_community_service.update_channel_for_user(
                user_document=user,
                channel_id=channel_id,
                data={
                    "name": payload.get("name"),
                    "description": payload.get("description"),
                },
            )
            return jsonify({"message": "Channel updated.", "channel": updated}), 200

        deleted = server_community_service.delete_channel_for_user(
            user_document=user,
            channel_id=channel_id,
        )
        if not deleted:
            return jsonify({"message": "Channel not found."}), 404
        return jsonify({"message": "Channel deleted."}), 200
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_activities_route():
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    page = _parse_int_arg(request.args.get("page"), 1)
    per_page = _parse_int_arg(request.args.get("per_page"), 20, max_value=100)
    filter_type = str(request.args.get("filter") or "all").strip().lower()
    payload = server_community_service.get_user_activity_feed(
        user_document=user,
        page=page,
        per_page=per_page,
        filter_type=filter_type,
    )
    return jsonify(payload)


def server_google_auth_route():
    payload = request.get_json(silent=True) or request.form
    id_token = str(payload.get("id_token") or "").strip()
    mode = str(payload.get("mode") or "login").strip().lower()

    try:
        user = server_community_service.authenticate_with_google(id_token=id_token, mode=mode)
        session["server_user_id"] = user.get("id")
        session["server_username"] = user.get("username")
        session["server_name"] = user.get("name")
        session["server_account_type"] = user.get("account_type")
        session["server_profile_image"] = user.get("profile_image")
        return jsonify({"message": "Google authentication successful.", "user": user}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_messages_route():
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    if request.method == "GET":
        channel_id = str(request.args.get("channel_id") or "").strip()
        if not channel_id:
            return jsonify({"message": "channel_id is required."}), 400
        page = _parse_int_arg(request.args.get("page"), 1)
        per_page = _parse_int_arg(request.args.get("per_page"), 50, max_value=50)
        search_query = str(request.args.get("search") or "").strip()
        parent_message_id = str(request.args.get("parent_message_id") or "").strip()
        pinned_only = _parse_bool_arg(request.args.get("pinned_only"), False)
        scope = str(request.args.get("scope") or "root").strip().lower()
        try:
            if parent_message_id:
                thread_data = server_community_service.get_thread_messages_for_channel(
                    user,
                    channel_id,
                    parent_message_id,
                    page=page,
                    per_page=per_page,
                    search_query=search_query,
                )
                return jsonify(
                    {
                        "thread_root": thread_data["root_message"],
                        "messages": thread_data["replies"],
                        "pagination": thread_data["pagination"],
                    }
                )

            if scope == "all":
                payload = server_community_service.get_channel_activity(
                    user,
                    channel_id,
                    page=page,
                    per_page=per_page,
                    search_query=search_query,
                )
            else:
                payload = server_community_service.get_messages_for_channel(
                    user,
                    channel_id,
                    page=page,
                    per_page=per_page,
                    search_query=search_query,
                    pinned_only=pinned_only,
                )
            return jsonify(payload)
        except PermissionError as exc:
            return jsonify({"message": str(exc)}), 403
        except Exception as exc:
            return jsonify({"message": str(exc)}), 400

    payload = request.get_json(silent=True) or request.form
    channel_id = str(payload.get("channel_id") or "").strip()
    text = str(payload.get("text") or "")
    parent_message_id = str(payload.get("parent_message_id") or "").strip()
    if not channel_id:
        return jsonify({"message": "channel_id is required."}), 400

    try:
        message = server_community_service.send_message(
            user,
            channel_id,
            text,
            parent_message_id=parent_message_id,
        )
        return jsonify({"message": "Message sent.", "data": message}), 201
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_files_route():
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    if request.method == "GET":
        channel_id = str(request.args.get("channel_id") or "").strip()
        if not channel_id:
            return jsonify({"message": "channel_id is required."}), 400
        page = _parse_int_arg(request.args.get("page"), 1)
        per_page = _parse_int_arg(request.args.get("per_page"), 50, max_value=50)
        search_query = str(request.args.get("search") or "").strip()
        try:
            payload = server_community_service.list_files_for_channel(
                user_document=user,
                channel_id=channel_id,
                page=page,
                per_page=per_page,
                search_query=search_query,
            )
            return jsonify(payload), 200
        except PermissionError as exc:
            return jsonify({"message": str(exc)}), 403
        except Exception as exc:
            return jsonify({"message": str(exc)}), 400

    channel_id = str(request.form.get("channel_id") or request.args.get("channel_id") or "").strip()
    if not channel_id:
        return jsonify({"message": "channel_id is required."}), 400
    upload = request.files.get("file")
    display_name = str(request.form.get("name") or "").strip()
    try:
        created = server_community_service.upload_file_to_channel(
            user_document=user,
            channel_id=channel_id,
            file_storage=upload,
            name=display_name,
        )
        return jsonify({"message": "File uploaded.", "data": created}), 201
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_update_file_route(file_id):
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    upload = request.files.get("file")
    display_name = str(request.form.get("name") or "").strip()
    try:
        updated = server_community_service.update_file_in_channel(
            user_document=user,
            file_id=file_id,
            name=display_name,
            file_storage=upload,
        )
        return jsonify({"message": "File updated.", "data": updated}), 200
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_delete_file_route(file_id):
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        deleted = server_community_service.delete_file_in_channel(user_document=user, file_id=file_id)
        if not deleted:
            return jsonify({"message": "File not found."}), 404
        return jsonify({"message": "File deleted."}), 200
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_user_profile_route(user_id):
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    channel_id = str(request.args.get("channel_id") or "").strip()
    if not channel_id:
        return jsonify({"message": "channel_id is required."}), 400

    try:
        payload = server_community_service.get_user_profile_for_channel(
            requester_user=user,
            target_user_id=user_id,
            channel_id=channel_id,
        )
        return jsonify({"user": payload}), 200
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_update_message_route(message_id):
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form
    text = str(payload.get("text") or "")
    try:
        message = server_community_service.update_message(user, message_id, text)
        return jsonify({"message": "Message updated.", "data": message}), 200
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_delete_message_route(message_id):
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        message = server_community_service.delete_message(user, message_id)
        return jsonify({"message": "Message deleted.", "data": message}), 200
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_react_message_route():
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form
    message_id = str(payload.get("message_id") or "").strip()
    emoji = str(payload.get("emoji") or "").strip()

    if not message_id:
        return jsonify({"message": "message_id is required."}), 400
    if not emoji:
        return jsonify({"message": "emoji is required."}), 400

    try:
        message = server_community_service.toggle_message_reaction(user, message_id, emoji)
        return jsonify({"message": "Reaction updated.", "data": message}), 200
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def server_pin_message_route():
    user = _get_server_user_doc()
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form
    message_id = str(payload.get("message_id") or "").strip()
    if not message_id:
        return jsonify({"message": "message_id is required."}), 400

    try:
        message = server_community_service.toggle_message_pin(user, message_id)
        return jsonify({"message": "Pin status updated.", "data": message}), 200
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def admin_server_user_list_route():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search_query = str(request.args.get("search") or "").strip()
    account_type_filter = str(request.args.get("account_type") or "").strip()
    order = (
        SortOrder.DESC
        if request.args.get("order", "desc").upper() == SortOrderStr.DESC
        else SortOrder.ASC
    )

    rows, total = server_community_service.get_paginated_users(
        page=page,
        per_page=per_page,
        order=order,
        search_query=search_query,
        account_type_filter=account_type_filter,
    )
    return jsonify(
        {
            "users": rows,
            "total_users": total,
            "total_pages": (total + per_page - 1) // per_page,
            "search": search_query,
            "account_type": account_type_filter,
        }
    )


def admin_add_server_user_route():
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    try:
        user = server_community_service.add_user_by_admin(
            {
                "name": payload.get("name"),
                "birthdate": payload.get("birthdate"),
                "place": payload.get("place"),
                "gender": payload.get("gender"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "password": payload.get("password"),
                "account_type": payload.get("account_type", "member"),
            }
        )
        return jsonify({"message": "Server user added.", "user": user}), 201
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def admin_update_server_user_route(user_id):
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    try:
        user = server_community_service.update_user_by_admin(
            user_id=user_id,
            data={
                "name": payload.get("name"),
                "birthdate": payload.get("birthdate"),
                "place": payload.get("place"),
                "gender": payload.get("gender"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "password": payload.get("password"),
                "account_type": payload.get("account_type"),
                "is_active": payload.get("is_active"),
            },
        )
        return jsonify({"message": "Server user updated.", "user": user}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def admin_delete_server_user_route(user_id):
    try:
        success = server_community_service.delete_user_by_admin(user_id)
        if not success:
            return jsonify({"message": "Server user not found."}), 404
        return jsonify({"message": "Server user deleted."}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def admin_server_channel_list_route():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search_query = str(request.args.get("search") or "").strip()
    type_filter = str(request.args.get("channel_type") or "").strip()
    visibility_filter = str(request.args.get("visibility") or "").strip()
    order = (
        SortOrder.DESC
        if request.args.get("order", "desc").upper() == SortOrderStr.DESC
        else SortOrder.ASC
    )

    rows, total = server_community_service.get_paginated_channels(
        page=page,
        per_page=per_page,
        order=order,
        search_query=search_query,
        type_filter=type_filter,
        visibility_filter=visibility_filter,
    )
    return jsonify(
        {
            "channels": rows,
            "total_channels": total,
            "total_pages": (total + per_page - 1) // per_page,
            "search": search_query,
        }
    )


def admin_add_server_channel_route():
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    admin_user = {
        "_id": "admin-session",
        "account_type": "admin",
    }
    try:
        channel = server_community_service.create_channel(
            user_document=admin_user,
            data={
                "name": payload.get("name"),
                "description": payload.get("description"),
                "channel_type": payload.get("channel_type", "custom"),
                "is_public": payload.get("is_public", True),
            },
        )
        return jsonify({"message": "Server channel added.", "channel": channel}), 201
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def admin_update_server_channel_route(channel_id):
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    try:
        channel = server_community_service.update_channel_by_admin(
            channel_id=channel_id,
            data={
                "name": payload.get("name"),
                "description": payload.get("description"),
                "channel_type": payload.get("channel_type"),
                "is_public": payload.get("is_public"),
            },
        )
        return jsonify({"message": "Server channel updated.", "channel": channel}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400


def admin_delete_server_channel_route(channel_id):
    try:
        success = server_community_service.delete_channel_by_admin(channel_id)
        if not success:
            return jsonify({"message": "Server channel not found."}), 404
        return jsonify({"message": "Server channel deleted."}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 400
