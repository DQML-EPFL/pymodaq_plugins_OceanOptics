# -*- coding: utf-8 -*-
"""
Created on Mon Feb 3 2025

@author: dqml-lab
"""

import ctypes
import numpy as np
from math import *
from oceandirect.OceanDirectAPI import OceanDirectAPI, OceanDirectError, FeatureID


class OceanView_Wrapper:

    ############## My methods

    def __init__(self, n_average) -> None:
        """
        Max Sampling Freq = 80 MHz
        """

        self.id = None
        self.api = OceanDirectAPI()
        self.device = None



    def initialize_spectro(self, n_average = 1, integration_time = 1):

        # ----------
        # Initialise Device
        # ----------

        
        # Find USB devices and IDs
        device_count = self.api.find_usb_devices()
        device_ids   = self.api.get_device_ids()

        device_count = len(device_ids)
        (major, minor, point) = self.api.get_api_version_numbers()

        # Load 
        if device_count == 0:
            print("No device Found")
            raise RuntimeError(f'No OceanOptics Device Found')
        else:
            for id in device_ids:
                self.id = id
                self.device = self.api.open_device(id)
                serialNumber = self.device.get_serial_number()
                self.device.set_scans_to_average( n_average )
                self.device.set_integration_time( int( integration_time * 1e3 ) )
                        

                print("API Version  : %d.%d.%d " % (major, minor, point))
                print("Total Device : %d     " % device_count)
                print("Serial Number: %s     " % serialNumber)

                print("Scan Averages : ", self.device.get_scans_to_average() )
                print("Integration Time : ", self.device.get_integration_time() )


        return True


    ############## PMD mandatory methods

    def get_the_x_axis(self):
        wavel = np.array( self.device.get_wavelengths() )
        return wavel

    def get_spectrum(self):

        # ----------
        # Get Data
        # ----------

        spectrum = self.device.get_formatted_spectrum() 
        
        return np.array( spectrum )


    def terminate_the_communication(self, manager, hit_except):
        try:
            self.device.close_device(self.id)
            print('Communication terminated')
            exit(manager)
            manager.close()

        except:
            hit_except = True









def main():
    spectro = OceanView_Wrapper()
    spectro.initialize_spectro()

    spectrum = spectro.get_spectrum()
    wavel = spectro.get_the_x_axis()

    import matplotlib.pyplot as plt
    plt.plot(wavel, spectrum)
    plt.show()




if __name__ == "__main__":
    main()