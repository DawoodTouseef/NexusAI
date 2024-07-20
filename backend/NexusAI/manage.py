#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

"""
"Added by ngrok"
    # This block handles 'make rundjangosite' which uses this manage.py as the entry point.
    # Set env variable to protect against the autoreloader.
    if os.getenv("NGROK_LISTENER_RUNNING") is None:
        os.environ["NGROK_LISTENER_RUNNING"] = "true"
        import asyncio, multiprocessing, ngrok

        async def setup():
            ngrok.set_auth_token('2Zlki2VMdQ0OvQEIl9DY50DzfdD_6gQiBym2A1SdtXfLtzUut')
            listen = sys.argv[2] if len(sys.argv) > 2 else "localhost:5000"
            listener = await ngrok.default()
            print(f"Forwarding to {listen} from ingress url: {listener.url()}")
            listener.forward(listen)

        asyncio.run(setup())
    "End added by ngrok"
"""
def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatBot.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()