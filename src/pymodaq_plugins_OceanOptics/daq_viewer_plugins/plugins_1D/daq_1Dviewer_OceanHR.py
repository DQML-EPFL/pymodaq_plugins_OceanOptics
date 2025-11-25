import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

from pymodaq_plugins_OceanOptics.hardware.oceandirect.OceanDirectAPI import OceanDirectAPI, OceanDirectError, FeatureID



class DAQ_1DViewer_OceanHR(DAQ_Viewer_base):
    """ Instrument plugin class for a 1D viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    Device : object
        Once loaded, holds the device that takes the aquisition
    
    """

    params = comon_parameters + [
        {'title': 'Integration time', 'name': 'integration_time', 'type': 'int', 'value': 10, 'min': 1, 'max': 10000, 'siPrefix': True, 'suffix': 'ms', 'tip': 'Integration time for spectrum aquisition.\nMIN=1ms, MAX=10000ms'},
        {'title': 'Scan Averaging', 'name': 'scan_average', 'type': 'int', 'value': 1, 'min': 1, 'max': 10000, 'siPrefix': True, 'suffix': ' Scans', 'tip': "Averaging over a certain number of scans. Reduces noise but doesn't increase signal strength."}
        ]
    

    def ini_attributes(self):
        self.device = None
        self.device_id = None

        self.x_axis = None



    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "integration_time":
           self.device.set_integration_time( int( self.settings["integration_time"] * 1e3 ) )
        
        if param.name() == "scan_average":
           self.device.set_scans_to_average( self.settings["scan_average"] )


    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.is_master:
            # Create Controller
            self.controller : OceanDirectAPI = OceanDirectAPI()
            
            # Find USB devices and IDs
            device_count = self.controller.find_usb_devices()
            device_ids   = self.controller.get_device_ids()

            device_count = len(device_ids)
            (major, minor, point) = self.controller.get_api_version_numbers()

            # Load 
            if device_count == 0:
                print("No device Found")
                raise RuntimeError(f'No OceanOptics Device Found')
            else:
                for id in device_ids:
                    self.id = id
                    self.device = self.controller.open_device(id)
                    serialNumber = self.device.get_serial_number()
                    self.device.set_scans_to_average( self.settings["scan_average"] )
                    self.device.set_integration_time( int( self.settings["integration_time"] * 1e3 ) )
                           

                    print("API Version  : %d.%d.%d " % (major, minor, point))
                    print("Total Device : %d     " % device_count)
                    print("Serial Number: %s     " % serialNumber)

                    print("Scan Averages : ", self.device.get_scans_to_average() )
                    print("Integration Time : ", self.device.get_integration_time() )


            initialized = True

        # Create x-axis
        wavel = np.array( self.device.get_wavelengths() )
        self.x_axis = Axis(data=wavel, label='', units='', index=0)

        info = "Success I think"
        return info, initialized



    def close(self):
        """Terminate the communication protocol"""
        self.cooller.close_device(self.id)


    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """

        spectrum = np.array( self.device.get_formatted_spectrum() )
        self.dte_signal.emit(DataToExport('Spectrum',
                                          data=[DataFromPlugins(name='Spectrum', data=spectrum,
                                                                dim='Data1D', labels=['dat0', 'Spectrum'],
                                                                axes=[self.x_axis])]))



    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        pass


    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        print("Stop Aquisition")

if __name__ == '__main__':
    main(__file__)
