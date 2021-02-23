import secrets
import serial
from serial.tools import list_ports


def trng3_random():
    blocksize = 1
    ports_avaiable = list(list_ports.comports())
    rng_com_port = None
    for temp in ports_avaiable:
        if temp[1].startswith("TrueRNG"):
            if rng_com_port == None:  # always chooses the 1st TrueRNG found
                rng_com_port = str(temp[0])
    try:
        ser = serial.Serial(port=rng_com_port, timeout=10)  # timeout set at 10 seconds in case the read fails
        if (ser.isOpen() == False):
            ser.open()
        ser.setDTR(True)
        ser.flushInput()
    except Exception:
        return
    try:
        x = ser.read(blocksize)  # read bytes from serial port
    except Exception:
        return
    ser.close()
    bin_ascii = bin(int(x.hex(), base=16))[2:].zfill(8 * blocksize)  # bin to ascii
    bin_ascii_2 = bin_ascii[0:2]
    if bin_ascii_2 == "00":
        return "Vermelho"
    elif bin_ascii_2 == "01":
        return "Amarelo"
    elif bin_ascii_2 == "10":
        return "Azul"
    else:
        return "Verde"

events_list = ["Amarelo", "Azul", "Verde", "Vermelho"]

lista = []
for i in range(1000):
    item = secrets.choice(events_list) # trng3_random() #
    lista.append(item)

print("Número de testes:", len(lista))
vermelho = lista.count("Vermelho")
amarelo = lista.count("Amarelo")
verde = lista.count("Verde")
azul = lista.count("Azul")

print("Vermelho:", vermelho/len(lista) * 100, "%")
print("Amarelo:", amarelo/len(lista) * 100, "%")
print("Verde:", verde/len(lista) * 100, "%")
print("Azul:", azul/len(lista) * 100, "%")
print("Total:", verde + vermelho + azul + amarelo)