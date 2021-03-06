#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings


def deprecate(old, new=None, version=None):
    """
    Decorator to raise deprecation warning.

    Args:
        old (str): description of the old method/function
        new (str or None): description of the new method/function
        version (str or None): version number, like 2.7.3-alpha
    """
    def _deprecate(func):
        def wrapper(*args, **kwargs):
            if new is None:
                comment = f"{old} is deprecated, version > {version}"
            else:
                comment = f"Please use {new} rather than {old}, version > {version}"
            warnings.warn(
                comment,
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return _deprecate


class SubsetNotFoundError(KeyError, ValueError):
    """
    Error when subset was failed with specified arguments.

    Args:
        country (str): country name
        country_alias (str or None): country name used in the dataset
        province (str or None): province name
        start_date (str or None): start date, like 22Jan2020
        end_date (str or None): end date, like 01Feb2020
        date (str or None): specified date, like 22Jan2020
        message (str or None): the other messages
    """

    def __init__(self, country, country_alias=None, province=None,
                 start_date=None, end_date=None, date=None, message=None):
        self.area = self._area(country, country_alias, province)
        self.date = self._date(start_date, end_date, date)
        self.message = "" if message is None else f" {message}"

    def __str__(self):
        return f"Records{self.message} in {self.area}{self.date} were not found."

    @staticmethod
    def _area(country, country_alias, province):
        """
        Error when subset was failed with specified arguments.

        Args:
            country (str): country name
            country_alias (str or None): country name used in the dataset
            province (str or None): province name

        Returns:
            str: area name
        """
        if country_alias is None or country == country_alias:
            c_alias_str = ""
        else:
            c_alias_str = f" ({country_alias})"
        province_str = "" if province is None else f"{province}, "
        return f"{province_str}{country}{c_alias_str}"

    @staticmethod
    def _date(start_date, end_date, date):
        """
        Error when subset was failed with specified arguments.

        Args:
            start_date (str or None): start date, like 22Jan2020
            end_date (str or None): end date, like 01Feb2020
            date (str or None): specified date, like 22Jan2020
        """
        if date is not None:
            return f" on {date}"
        start_str = "" if start_date is None else f" from {start_date}"
        end_str = "" if end_date is None else f" to {end_date}"
        return f"{start_str}{end_str}"


class ScenarioNotFoundError(KeyError):
    """
    Error when unregistered scenario name was specified.

    Args:
        name (str): scenario name
    """

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name} scenario is not registered."


class UnExecutedError(AttributeError, NameError, ValueError):
    """
    Error when we have unexecuted methods that we need to run in advance.

    Args:
        method_name (str): method name to run in advance
        message (str or None): the other messages
    """

    def __init__(self, method_name, message=None):
        self.method_name = method_name
        self.message = "." if message is None else f" {message}."

    def __str__(self):
        return f"Please execute {self.method_name} in advance{self.message}"


class PCRIncorrectPreconditionError(KeyError):
    """
    Error when checking preconditions in the PCR data.

    Args:
        country (str): country name
        province (str or None): province name
        message (str or None): the other messages
    """

    def __init__(self, country, province=None, message=None):
        self.area = self._area(country, province)
        self.message = "" if message is None else f" {message}"

    def __str__(self):
        return f"{self.message}{self.area}."

    @staticmethod
    def _area(country, province):
        """
        Error when PCR preconditions failed with specified arguments.

        Args:
            country (str): country name
            province (str or None): province name

        Returns:
            str: area name
        """
        country_str = (" in country " + country) if not province else ""
        province_str = "" if province is None else (" in province " + province)
        return f"{province_str}{country_str}"
