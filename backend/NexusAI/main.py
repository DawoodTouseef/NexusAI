import os
import argparse
import subprocess

def start_app(args):
    try:
        path = os.path.join(os.getcwdb().decode(), "manage.py")
        subprocess.run(['python3', path, 'runserver', f"{args.host}:{args.port}"])
    except KeyboardInterrupt as e:
        print("server Stopped!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="Port Number to Host", default=5000)
    parser.add_argument("--host", default="0.0.0.0", help="Name of the Host")

    args = parser.parse_args()

    start_app(args)
