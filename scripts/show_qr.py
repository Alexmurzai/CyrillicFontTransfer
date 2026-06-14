import sys
import os

try:
    import qrcode
    url = sys.argv[1] if len(sys.argv) > 1 else "https://alexmurzai.github.io/CyrillicFontTransfer/"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    
    # Save as PNG
    img = qr.make_image(fill_color="black", back_color="white")
    temp_dir = os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__)))
    qr_path = os.path.join(temp_dir, 'moct_mobile_qr.png')
    img.save(qr_path)
    
    print()
    print(f"  [OK] Generated QR Code image: {qr_path}")
    print("  [OK] Opening QR Code image in your default viewer...")
    
    # Open image using default OS program
    os.startfile(qr_path)
    
    print()
    print("  Scan the opened QR code with your phone camera!")
    print()
except ImportError:
    print("  [TIP] Install qrcode & pillow: pip install qrcode pillow")
    print("  For now, copy the URL manually.")
    print()
except Exception as e:
    # Fallback to ascii representation if anything fails
    print(f"  Failed to save/open PNG: {e}")
    try:
        # Retry with ascii printing in console
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        print("  Scan the console QR code with your phone camera!")
    except Exception as ascii_err:
        print(f"  Console QR print failed: {ascii_err}")
    print()
