import pyvisa

# Inizializzazione del ResourceManager PyVISA con backend puro Python
rm = pyvisa.ResourceManager('@py')
print(rm.list_resources())