import frappe
from .utils import create_logger

logger = create_logger()

ADMIN_CHANNEL_NAME = "general"  # change to your Raven channel name/id


def _resolve_channel(channel_name=ADMIN_CHANNEL_NAME):
    """Find the Raven Channel by name."""
    channel = frappe.db.get_value(
        "Raven Channel",
        {"channel_name": channel_name},
        "name",
    )
    if not channel:
        raise frappe.DoesNotExistError(f"Raven Channel '{channel_name}' not found")
    return channel


def send_message(text, channel_name=ADMIN_CHANNEL_NAME):
    """Post a message into a Raven channel by inserting a Raven Message doc."""
    try:
        channel_id = _resolve_channel(channel_name)

        msg = frappe.get_doc({
            "doctype": "Raven Message",
            "channel_id": channel_id,
            "text": text,
            "message_type": "Text",
        })
        msg.insert(ignore_permissions=True)
        frappe.db.commit()

        logger.info(f"Raven message sent to '{channel_name}' ({msg.name})")
        return msg.name

    except Exception as e:
        logger.error(f"Failed to send Raven message: {e}")
        frappe.log_error(frappe.get_traceback(), "Daily Timesheet Summary - Raven")
        raise
