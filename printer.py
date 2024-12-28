import win32print
import win32ui
from PIL import Image, ImageWin



def physical_print(path):
    # Constants for printer dimensions
    PHYSICALWIDTH = 110
    PHYSICALHEIGHT = 117

    # Get default printer
    printer_name = win32print.GetDefaultPrinter()

    # Create a device context for the printer
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)

    # Get the printer's physical dimensions
    printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
    # print(printer_size)
    # exit()
    # Load the image and rotate it if needed
    bmp = Image.open(path)
    if bmp.size[0] < bmp.size[1]:
        bmp = bmp.rotate(90, expand=True)

    # Start the document
    hDC.StartDoc(path)
    hDC.StartPage()

    # Draw the image on the printer canvas
    dib = ImageWin.Dib(bmp)
    dib.draw(hDC.GetHandleOutput(), (0, 0, printer_size[0], printer_size[1]))

    # End the page and document
    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()
