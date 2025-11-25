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

    TODO Complete the docstring of your plugin with:
        * The set of instruments that should be compatible with this instrument plugin.
        * With which instrument it has actually been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    # TODO add your particular attributes here if any

    """
    params = comon_parameters+[
        ## TODO for your custom plugin
        # elements to be added here as dicts in order to control your custom stage
        ############
        ]
    

    def ini_attributes(self):
        #  TODO declare the type of the wrapper (and assign it to self.controller) you're going to use for easy
        #  autocompletion
        # self.controller : OceanDirectAPI = OceanDirectAPI()

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
        ## TODO for your custom plugin
        if param.name() == "a_parameter_you've_added_in_self.params":
           self.controller.your_method_to_apply_this_param_change()
#        elif ...
        ##

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
            self.controller : OceanDirectAPI = OceanDirectAPI()
            
            device_count = self.controller.find_usb_devices()
            device_ids   = self.controller.get_device_ids()

            device_count = len(device_ids)
            (major, minor, point) = self.controller.get_api_version_numbers()

            if device_count == 0:
                print("No device Found")
                raise RuntimeError 
            else:
                for id in device_ids:
                    self.id = id
                    self.device = self.controller.open_device(id)
                    serialNumber = self.device.get_serial_number()
                    self.device.set_scans_to_average(1)             
                    self.device.set_integration_time(int(1e3))  
                           

                    print("API Version  : %d.%d.%d " % (major, minor, point))
                    print("Total Device : %d     " % device_count)
                    print("Serial Number: %s     " % serialNumber)

                    print("Scan Averages : ", self.device.get_scans_to_average() )
                    print("Integration Time : ", self.device.get_integration_time() )


            initialized = True


        # ## TODO for your custom plugin☺
        wavel = np.array( self.device.get_wavelengths() )
        self.x_axis = Axis(data=wavel, label='', units='', index=0)

        # # get the x_axis (you may want to to this also in the commit settings if x_axis may have changed
        # data_x_axis = self.controller.your_method_to_get_the_x_axis()  # if possible
        # self.x_axis = Axis(data=data_x_axis, label='', units='', index=0)

        # # TODO for your custom plugin. Initialize viewers pannel with the future type of data
        # self.dte_signal_temp.emit(DataToExport(name='myplugin',
        #                                        data=[DataFromPlugins(name='Mock1',
        #                                                              data=[np.array([0., 0., ...]),
        #                                                                    np.array([0., 0., ...])],
        #                                                              dim='Data1D', labels=['Mock1', 'label2'],
        #                                                              axes=[self.x_axis])]))

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

        ##synchrone version (blocking function)
        spectrum = np.array( self.device.get_formatted_spectrum() )
        self.dte_signal.emit(DataToExport('Spectrum',
                                          data=[DataFromPlugins(name='Spectrul', data=spectrum,
                                                                dim='Data1D', labels=['dat0', 'data1'],
                                                                axes=[self.x_axis])]))

        # ##asynchrone version (non-blocking function with callback)
        # self.controller.your_method_to_start_a_grab_snap(self.callback)
        # #########################################################


    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        data_tot = self.controller.your_method_to_get_data_from_buffer()
        self.dte_signal.emit(DataToExport('myplugin',
                                          data=[DataFromPlugins(name='Mock1', data=data_tot,
                                                                dim='Data1D', labels=['dat0', 'data1'])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        ## TODO for your custom plugin
        raise NotImplementedError  # when writing your own plugin remove this line
        self.controller.your_method_to_stop_acquisition()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))
        ##############################
        return ''


if __name__ == '__main__':
    main(__file__)
