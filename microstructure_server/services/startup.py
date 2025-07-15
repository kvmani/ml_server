from config import Config

config = Config()


def start_services():
    print("\nChecking ML model service...")
    if not config.start_ml_model_service():
        print("Warning: ML model service could not be started. Some features may not work.")
    else:
        print("ML model service is running!")

    print("\nChecking EBSD model service...")
    if not config.start_ebsd_model_service():
        print("Warning: EBSD model service could not be started. EBSD features may not work.")
    else:
        print("EBSD model service is running!")
