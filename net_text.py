# net_probe.py
import urllib.request, ssl, traceback

URL = "https://clients3.google.com/generate_204"

def main():
    print("Probing HTTPS:", URL)
    try:
        r = urllib.request.urlopen(URL, timeout=5)
        print("HTTP status:", r.status)   # 정상일 때 204
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()