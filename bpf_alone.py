#!/usr/bin/env python
"""Subsystem A unit testing script.
This script measures the frequency response of the pre-mixer BPF."""

import pyvisa
import time
from numpy import *
from matplotlib.pyplot import *
import sys

__author__ = 'Sean Victor Hum'
__copyright__ = 'Copyright 2023'
__license__ = 'GPL'
__version__ = '1.0'
__email__ = 'sean.hum@utoronto.ca'

def user_prompt():
    str = input('Hit Enter to proceed or ! to abort:')
    if (str == '!'):
        print('Measurement aborted')
        user_abort()

def user_abort():
        scope.write(':WGEN:OUTP OFF')
        fxngen.write('OUTPut1 OFF')
        fxngen.write('OUTPut2 OFF')
        scope.close()
        fxngen.close()
        sys.exit(0)
        
# Open instrument connection(s)
rm = pyvisa.ResourceManager()
school_ip = True
#school_ip = False
if (school_ip):
    scope = rm.open_resource('TCPIP0::192.168.0.253::hislip0::INSTR')
    fxngen = rm.open_resource('TCPIP0::192.168.0.254::5025::SOCKET')
else:
    scope = rm.open_resource('TCPIP0::192.168.2.253::hislip0::INSTR')
    fxngen = rm.open_resource('TCPIP0::192.168.2.254::5025::SOCKET')

# Define string terminations and timeouts
scope.write_termination = '\n'
scope.read_termination = '\n'
fxngen.write_termination = '\n'
fxngen.read_termination = '\n'
scope.timeout = 10000           # 10s
fxngen.timeout = 10000          # 10s

# Get ID info
scope_id = scope.query('*IDN?').strip().split(',')
fxngen_id = fxngen.query('*IDN?').strip().split(',')
print('Connected to oscilloscope:', scope_id[1], flush=True)
print('Connected to function generator:', fxngen_id[1], flush=True)

# Set probe scaling to 1:1
scope.write('CHANnel1:PROBe +1.0')

# Setup trigger
scope.write(':TRIG:SWEep AUTO')
scope.write(':TRIG:EDGE:SOURce CHAN1')
scope.write(':TRIG:EDGE:LEVel +0.0')

#print('Trigger:', scope.query(':TRIG?'), flush=True)

print('Please skip this message. No need to de-assert /TXEN.')
user_prompt()

# Set waveform generator output impedance to high Z
fxngen.write('OUTPUT1:LOAD INF')
fxngen.write('UNIT:ANGL DEG')

# Setup waveform generator
input_ampl = 100E-3
fxngen.write('SOUR1:FUNCtion SIN')
fxngen.write('SOUR1:VOLTage:HIGH +50E-3')
fxngen.write('SOUR1:VOLTage:LOW -50E-3')
fxngen.write('SOUR1:PHASe:SYNC')
fxngen.write('SOUR1:PHASe +0.0')
fxngen.write('OUTPut1 ON')

# Setup acquisition
scope.write(':TIMebase:SCAL +5.0E-04') # 500 us/div
scope.write(':CHAN1:COUP AC')

# Frequency sweep
N = 51
freq = arange(N)/(N-1)*20e6 + 2e6

# Set up instruments for first frequency point
fxngen.write('SOUR1:FREQuency %e' % (2e6))

print('The following frequency points will be measured:', freq)

# Initialize vectors for storing data
ampl_i = zeros(N, float)
#phdiff = zeros(N, float)

print('Adjust the timebase and triggering so the signals are stable.')
user_prompt()

# Frequency sweep loop
scope.write(':TIMebase:SCAL +2.0E-04') 
for k in range(N):
    fxngen.write('SOUR1:FREQuency %e' % freq[k])
    time.sleep(0.5)
    #scope.write(':SINGle')
    ampl_i[k] = float(scope.query(':MEAS:VPP? CHAN1'))
    #phdiff[k] = float(scope.query(':MEAS:PHASe? CHAN1'))
    print('Frequency point %d/%d, f=%.2f MHz: %f' % (k+1, N, freq[k]/1e6, ampl_i[k]))

print('Done')
    
fxngen.write('OUTPut1 OFF')
fxngen.close()
scope.close()
    
# Save and plot data
savetxt('bpf_alone.txt', (freq, ampl_i))

H2 = (ampl_i/input_ampl)**2

fig, ax = subplots()
ax.plot(freq/1e6, 10*log10(H2))
ax.set_xlabel('Frequency [MHz]');
ax.set_ylabel('BPF gain [dB]');
ax.grid(True)
ax.set_title('Frequency response of BPF')
savefig('bpf_alone.png')