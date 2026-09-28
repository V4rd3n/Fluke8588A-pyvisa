import pyvisa

# Inizializzazione del ResourceManager PyVISA con backend puro Python
rm = pyvisa.ResourceManager('@py')

# Formattazione della risorsa SOCKET: TCPIP0::<IP_STRUMENTO>::<PORTA>::SOCKET
resource_name = 'TCPIP0::192.168.0.250::3490::SOCKET'

try:
    # Apertura diretta senza passare da list_resources()
    inst = rm.open_resource(resource_name)
    
    # Per i socket raw Ethernet occorre configurare esplicitamente la terminazione LF (\n)
    inst.read_termination = '\n'
    inst.write_termination = '\n'
    inst.timeout = 5000  # Timeout in millisecondi
    
    # Test di comunicazione SCPI
    idn_response = inst.query('*IDN?')
    print("Risposta dallo strumento:", idn_response)

except pyvisa.errors.VisaIOError as e:
    print(f"Errore I/O VISA: {e}")
except Exception as e:
    print(f"Errore generico: {e}")