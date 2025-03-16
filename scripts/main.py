from interface import FlightPricesChecker
from controller import FlightsController


if __name__ == "__main__":
    controller = FlightsController()

    app = FlightPricesChecker(controller)
    app.run()
