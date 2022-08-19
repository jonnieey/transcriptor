from abc import ABC, abstractmethod

from transcriptor.models import ConfigModel


class View(ABC):
    @abstractmethod
    def show_item_list(self, item_type, item_list):
        pass

    @abstractmethod
    def show_item_information(self, item_type, item_name, item_info):
        pass


class ConsoleView(View):
    def show_item_list(self, item_type, item_list):
        for item in item_list:
            print(item)
        print("")

    def show_item_information(self, item_type, item_name, item_info):
        print(f"{item_name} -> {item_info}")


if __name__ == "__main__":
    c = ConfigModel(date_format="%m-%Y", base_dir="base/dir")
    v = ConsoleView()
    v.show_item_list(c.item_type, list(c))
    v.show_item_information(c.item_type, "config", dict(c))
