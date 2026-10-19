
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List
import re


class NotificationStatus(Enum):
    PENDING = "Pending"
    SENT = "Sent"
    FAILED = "Failed"


@dataclass
class Notification(ABC):
    notification_id: int
    recipient: str
    message: str
    fail_attempts: int = 0
    status: NotificationStatus = NotificationStatus.PENDING
    attempts: int = 0
    created_time: datetime = field(default_factory=datetime.now)
    history: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.recipient = self.recipient.strip()
        self.message = self.message.strip()

        if not self.recipient:
            raise ValueError("Recipient cannot be empty.")
        if not self.message:
            raise ValueError("Message cannot be empty.")
        if self.fail_attempts < 0:
            raise ValueError("Failure attempts cannot be negative.")

        self.history.append(
            f"{self.created_time.isoformat(timespec='seconds')}: "
            "Notification created."
        )

    @property
    @abstractmethod
    def channel(self) -> str:
        pass

    @abstractmethod
    def validate_recipient(self) -> bool:
        pass

    def send(self) -> bool:
        """Simulate notification delivery."""
        if self.status == NotificationStatus.SENT:
            raise ValueError("Notification has already been sent.")

        self.attempts += 1

        if not self.validate_recipient():
            self.status = NotificationStatus.FAILED
            self.history.append(
                f"Attempt {self.attempts}: invalid recipient."
            )
            return False

        if self.fail_attempts > 0:
            self.fail_attempts -= 1
            self.status = NotificationStatus.FAILED
            self.history.append(
                f"Attempt {self.attempts}: simulated delivery failure."
            )
            return False

        self.status = NotificationStatus.SENT
        self.history.append(
            f"Attempt {self.attempts}: notification sent successfully."
        )
        return True


class EmailNotification(Notification):
    @property
    def channel(self) -> str:
        return "Email"

    def validate_recipient(self) -> bool:
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        return bool(re.fullmatch(pattern, self.recipient))


class SMSNotification(Notification):
    @property
    def channel(self) -> str:
        return "SMS"

    def validate_recipient(self) -> bool:
        return bool(re.fullmatch(r"\+?[0-9]{7,15}", self.recipient))


class WhatsAppNotification(Notification):
    @property
    def channel(self) -> str:
        return "WhatsApp"

    def validate_recipient(self) -> bool:
        return bool(re.fullmatch(r"\+?[0-9]{7,15}", self.recipient))


class NotificationService:
    def __init__(self):
        self.notifications: Dict[int, Notification] = {}
        self.next_id = 1

    def add_notification(
        self,
        channel: str,
        recipient: str,
        message: str,
        fail_attempts: int = 0,
    ) -> Notification:
        if not isinstance(channel, str):
            raise ValueError("Channel must be text.")

        channel = channel.strip().lower()

        classes = {
            "email": EmailNotification,
            "sms": SMSNotification,
            "whatsapp": WhatsAppNotification,
        }

        notification_class = classes.get(channel)
        if notification_class is None:
            raise ValueError(
                "Invalid channel. Choose Email, SMS, or WhatsApp."
            )

        notification = notification_class(
            notification_id=self.next_id,
            recipient=recipient,
            message=message,
            fail_attempts=fail_attempts,
        )

        self.notifications[self.next_id] = notification
        self.next_id += 1
        return notification

    def get_notification(self, notification_id: int) -> Notification:
        if notification_id not in self.notifications:
            raise KeyError(
                f"Notification ID {notification_id} was not found."
            )
        return self.notifications[notification_id]

    def send_notification(self, notification_id: int) -> bool:
        return self.get_notification(notification_id).send()

    def get_status(self, notification_id: int) -> str:
        return self.get_notification(notification_id).status.value

    def retry_notification(self, notification_id: int) -> bool:
        notification = self.get_notification(notification_id)

        if notification.status != NotificationStatus.FAILED:
            raise ValueError("Only failed notifications can be retried.")

        return notification.send()

    def get_all_notifications(self) -> List[Notification]:
        return list(self.notifications.values())

    def get_history(self, notification_id: int) -> List[str]:
        return list(self.get_notification(notification_id).history)


def display_notification(notification: Notification) -> None:
    print("-" * 45)
    print(f"ID:        {notification.notification_id}")
    print(f"Channel:   {notification.channel}")
    print(f"Recipient: {notification.recipient}")
    print(f"Message:   {notification.message}")
    print(f"Status:    {notification.status.value}")
    print(f"Attempts:  {notification.attempts}")
    print(f"Created:   {notification.created_time:%Y-%m-%d %H:%M:%S}")
    print("-" * 45)


def run_cli() -> None:
    service = NotificationService()

    while True:
        print("\n===== OOP NOTIFICATION SYSTEM =====")
        print("1. Add and send notification")
        print("2. View all notifications")
        print("3. Check notification status")
        print("4. Retry failed notification")
        print("5. View notification history")
        print("6. Exit")

        choice = input("Enter your choice: ").strip()

        try:
            if choice == "1":
                channel = input(
                    "Channel (Email/SMS/WhatsApp): "
                ).strip()
                recipient = input("Recipient: ").strip()
                message = input("Message: ").strip()

                notification = service.add_notification(
                    channel, recipient, message
                )
                print(f"Notification ID: {notification.notification_id}")

                if service.send_notification(notification.notification_id):
                    print("Notification sent successfully.")
                else:
                    print("Notification failed. You can retry it.")

                display_notification(notification)

            elif choice == "2":
                notifications = service.get_all_notifications()
                if not notifications:
                    print("No notifications found.")
                else:
                    for notification in notifications:
                        display_notification(notification)

            elif choice == "3":
                notification_id = int(input("Enter notification ID: "))
                print("Status:", service.get_status(notification_id))

            elif choice == "4":
                notification_id = int(input("Enter notification ID: "))
                if service.retry_notification(notification_id):
                    print("Retry successful!")
                else:
                    print("Retry failed. You can try again.")

            elif choice == "5":
                notification_id = int(input("Enter notification ID: "))
                for event in service.get_history(notification_id):
                    print(event)

            elif choice == "6":
                print("Thank you for using the Notification System.")
                break

            else:
                print("Invalid choice. Please select 1 to 6.")

        except (ValueError, KeyError) as error:
            print("Error:", error)


if __name__ == "__main__":
    run_cli()
