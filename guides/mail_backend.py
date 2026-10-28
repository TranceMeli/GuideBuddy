"""Mail backend for development: writes e-mails readably to the terminal.

The regular console backend prints the "raw" message (quoted-printable, i.e. with "=3D"
and line breaks in the middle of links). This one shows subject and body as plain text,
so confirmation links can be copied directly.
"""

from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend


class ReadableConsoleEmailBackend(ConsoleEmailBackend):
    def write_message(self, message):
        lines = [
            "",
            "=" * 79,
            "E-MAIL (development only, not sent)",
            f"From:    {message.from_email}",
            f"To:      {', '.join(message.to)}",
            f"Subject: {message.subject}",
            "-" * 79,
            message.body,
            "=" * 79,
            "",
        ]
        self.stream.write("\n".join(lines))
