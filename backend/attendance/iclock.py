"""
ZKTeco ADMS / "iclock" push protocol (also used by eSSL, Hikvision-ZK OEMs and many other terminals).

Configure the device: Menu → Comm. → Cloud Server Setting (or "ADMS"):
    Server address = this server's IP / domain, Server port = 80/443/8000, HTTPS as applicable.
Then register the device's serial number in the portal (Attendance → Biometric devices).

Protocol summary
    GET  /iclock/cdata?SN=...&options=all      → device asks for its options (handshake)
    POST /iclock/cdata?SN=...&table=ATTLOG     → device uploads punches, one per line
    GET  /iclock/getrequest?SN=...              → device polls for commands ("OK" = none)
    POST /iclock/devicecmd?SN=...               → device reports command results
"""
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .biometric import BiometricError, parse_zk_attlog, record_punches
from .models import BiometricDevice


def _text(body, status=200):
    return HttpResponse(body, content_type="text/plain", status=status)


def _device(request):
    sn = (request.GET.get("SN") or request.GET.get("sn") or "").strip()
    if not sn:
        return None
    return BiometricDevice.objects.filter(serial_number=sn, is_active=True).first()


def _tz_hours():
    offset = timezone.localtime().utcoffset()
    return int(offset.total_seconds() // 3600) if offset else 0


@csrf_exempt
def cdata(request):
    device = _device(request)
    if not device:
        return _text("ERROR: device not registered", 403)
    device.last_seen = timezone.now()
    device.save(update_fields=["last_seen"])
    if request.method == "GET":
        return _text("\n".join([
            f"GET OPTION FROM: {device.serial_number}",
            "ATTLOGStamp=None", "OPERLOGStamp=9999", "ATTPHOTOStamp=None",
            "ErrorDelay=30", "Delay=10", "TransTimes=00:00;14:05", "TransInterval=1",
            "TransFlag=TransData AttLog", f"TimeZone={_tz_hours()}", "Realtime=1", "Encrypt=None",
        ]) + "\n")
    table = (request.GET.get("table") or "").upper()
    if table != "ATTLOG":
        return _text("OK")  # OPERLOG, ATTPHOTO, BIODATA, USERINFO... are acknowledged and ignored
    try:
        rows = parse_zk_attlog(request.body.decode("utf-8", errors="ignore"))
        result = record_punches(device, rows, "push")
    except BiometricError as e:
        return _text(f"ERROR: {e}", 400)
    return _text(f"OK: {result['received']}")


@csrf_exempt
def getrequest(request):
    device = _device(request)
    if not device:
        return _text("ERROR: device not registered", 403)
    device.last_seen = timezone.now()
    device.save(update_fields=["last_seen"])
    return _text("OK")


@csrf_exempt
def devicecmd(request):
    return _text("OK")
