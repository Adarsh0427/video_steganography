import traceback

from PyQt5.QtWidgets import QMessageBox



class ErrorHandler:
    """
    Utility class for error handling and logging
    """
    
    @staticmethod
    def show_error_message(parent, title, message):
        """
        Show error message dialog
        
        Args:
            parent: Parent widget
            title (str): Dialog title
            message (str): Error message
        """
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_warning_message(parent, title, message):
        """
        Show warning message dialog
        
        Args:
            parent: Parent widget
            title (str): Dialog title
            message (str): Warning message
        """
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_info_message(parent, title, message):
        """
        Show information message dialog
        
        Args:
            parent: Parent widget
            title (str): Dialog title
            message (str): Information message
        """
        QMessageBox.information(parent, title, message)
       
    


        
    @staticmethod
    def handle_error(parent, e, title="Error", context=""):
        """
        Handle exception with logging and UI message
        
        Args:
            parent: Parent widget
            e (Exception): Exception object
            title (str): Error dialog title
            context (str): Context information
        """
        error_message = f"{context} - {str(e)}" if context else str(e)
        ErrorHandler.show_error_message(parent, title, error_message)
    
    @staticmethod
    def validate_input(parent, condition, error_message):
        """
        Validate input condition
        
        Args:
            parent: Parent widget
            condition (bool): Condition to validate
            error_message (str): Error message to show if condition fails
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not condition:
            ErrorHandler.show_error_message(parent, "Input Error", error_message)
            return False
        return True 