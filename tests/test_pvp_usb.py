import pyvisa

# Inizializzazione del ResourceManager PyVISA con backend puro Python
rm = pyvisa.ResourceManager('@py')
print(rm.list_resources())
inst = rm.open_resource("USB0::3966::32777::651684161::0::INSTR")
print(inst.query("SYST:TEMP?"))