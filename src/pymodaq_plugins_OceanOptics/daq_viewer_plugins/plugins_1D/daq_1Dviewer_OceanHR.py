import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_data.data import DataToExport, Axis
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

from scipy.optimize import curve_fit

from pymodaq_plugins_OceanOptics.hardware.OceanView_Wrapper import OceanView_Wrapper


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
        {'title': 'Averaging', 'name': 'scan_average', 'type': 'int', 'value': 1, 'min': 10, 'max': 10000, 'siPrefix': True, 'suffix': ' Trace', 'tip': "Averaging over a certain number of trace. Reduces noise but doesn't increase signal strength."},
        {'title': 'Fit', 'name': 'fit', 'type': 'bool', 'value': False, 'tip': "Try to fit the scan."}
        ]
    

    def ini_attributes(self):
        self.device = None
        self.device_id = None
        self.controller : OceanView_Wrapper = None

        self.x_axis = None
        self.manager = None
        self.hit_except = None



    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "integration_time":
           self.controller.device.set_integration_time( int( self.settings["integration_time"] * 1e3 ) )
        
        if param.name() == "scan_average":
           self.controller.device.set_scans_to_average( self.settings["scan_average"] )


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
            self.controller = OceanView_Wrapper()
            initialized = self.controller.initialize_spectro( 
                                                        n_average           = self.settings["scan_average"],
                                                        integration_time    = self.settings["integration_time"])
 

        info = "Success"
        return info, initialized


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

        spectrum = self.controller.get_spectrum()

        # Create x-axis
        self.x_axis = Axis(data=self.controller.get_the_x_axis() * 1e-9, units='m', index=0)
        
        # --- Create Pymodaq Data Structure     #TODO: Labels with no error
        dwa = DataFromPlugins(name='Spectrum', data=spectrum, dim='Data1D', axes=[self.x_axis])

        data_to_export = [ dwa ]

        # Try to fit
        if self.settings["fit"]: 
            try:
                popt, err=fit_trace(self.x_axis.data, spectrum)
                if err<100:  data_to_export = [ DataFromPlugins(name='Spectrum', data=[spectrum, gaussian(self.x_axis.data, *popt)], dim='Data1D', labels=['Trace', f'Fit : {popt[1]}'], axes=[self.x_axis])]

            except Exception as e: pass


        self.dte_signal.emit( DataToExport('Spectrum', data=data_to_export) )



    def close(self):
        """Terminate the communication protocol"""
        self.controller.terminate_the_communication(self.manager, self.hit_except)




def fit_trace(wavelen, spectrum):
    popt, pcov = curve_fit(gaussian, wavelen, spectrum, p0=[ spectrum.max()-spectrum.min(), wavelen[np.argmax(spectrum)], (wavelen[1]-wavelen[0])/5, spectrum.min() ], maxfev=1000)
    return popt, np.diag(pcov).sum() * np.sqrt(2)

def gaussian(x, A, x0, sigma, offset):
    return A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2)) + offset


if __name__ == '__main__':
    main(__file__)
