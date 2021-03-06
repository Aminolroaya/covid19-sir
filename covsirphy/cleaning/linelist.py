#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import swifter
from covsirphy.util.error import SubsetNotFoundError
from covsirphy.cleaning.cbase import CleaningBase


class LinelistData(CleaningBase):
    """
    Linelist of case reports.

    Args:
        filename (str or pathlib.path): CSV filename to save the raw dataset
        force (bool): if True, always download the dataset from the server
        verbose (int): level of verbosity
    """
    GITHUB_URL = "https://raw.githubusercontent.com"
    URL = f"{GITHUB_URL}/beoutbreakprepared/nCoV2019/master/latest_data/latestdata.tar.gz"
    # Column names
    AGE = "Age"
    SEX = "Sex"
    HOSPITAL_DATE = "Hospitalized_date"
    CONFIRM_DATE = "Confirmation_date"
    SYMPTOM = "Symptoms"
    CHRONIC = "Chronic_disease"
    OUTCOME = "Outcome"
    OUTCOME_DATE = "Outcome_date"
    R_DATE = "Recovered_date"
    F_DATE = "Fatal_date"
    LINELIST_COLS = [
        CleaningBase.COUNTRY, CleaningBase.PROVINCE,
        HOSPITAL_DATE, CONFIRM_DATE, OUTCOME_DATE,
        CleaningBase.C, CleaningBase.CI, CleaningBase.R, CleaningBase.F,
        SYMPTOM, CHRONIC, AGE, SEX,
    ]

    def __init__(self, filename, force=False, verbose=1):
        if Path(filename).exists() and not force:
            self._raw = self.load(filename)
        else:
            Path(filename).parent.mkdir(exist_ok=True, parents=True)
            self._raw = self._retrieve(filename=filename, verbose=verbose)
        self._cleaned_df = self._cleaning()
        self._citation = "Xu, B., Gutierrez, B., Mekaru, S. et al. " \
            "Epidemiological data from the COVID-19 outbreak, real-time case information. " \
            "Sci Data 7, 106 (2020). https://doi.org/10.1038/s41597-020-0448-0"
        # To avoid "imported but unused"
        self.__swifter = swifter

    def _retrieve(self, filename, verbose=1):
        """
        Retrieve the dataset from server.

        Args:
            filename (str or pathlib.path): CSV filename to save the raw dataset
            verbose (int): level of verbosity

        Returns:
            pd.DataFrame: raw dataset
        """
        # Show URL
        if verbose:
            print(
                "Retrieving linelist from Open COVID-19 Data Working Group repository: https://github.com/beoutbreakprepared/nCoV2019")
        # Download the dataset
        df = self.load(self.URL, header=1)
        # Remove un-necessary columns
        df = df.drop(
            [
                "Unnamed: 0", "city", "latitude", "longitude", "geo_resolution",
                "lives_in_Wuhan", "travel_history_dates", "travel_history_location",
                "reported_market_exposure", "additional_information",
                "chronic_disease_binary", "source", "sequence_available",
                "notes_for_discussion", "location", "admin3", "admin2", "admin1",
                "country_new", "admin_id", "data_moderator_initials",
                "travel_history_binary",
            ],
            axis=1,
            errors="ignore"
        )
        # Save the raw data
        df.to_csv(filename, index=False)
        return df

    def _cleaning(self):
        """
        Perform data cleaning of the raw data.

        Returns:
            pandas.DataFrame: cleaned data
        """
        df = self._raw.copy()
        # Rename columns
        df = df.rename(
            {
                "age": self.AGE,
                "sex": self.SEX,
                "province": self.PROVINCE,
                "country": self.COUNTRY,
                "date_admission_hospital": self.HOSPITAL_DATE,
                "date_confirmation": self.CONFIRM_DATE,
                "symptoms": self.SYMPTOM,
                "chronic_disease": self.CHRONIC,
                "outcome": self.OUTCOME,
                "date_death_or_discharge": self.OUTCOME_DATE,
            },
            axis=1
        )
        # Location
        df = df.dropna(subset=[self.COUNTRY])
        df[self.PROVINCE] = df[self.PROVINCE].fillna(self.UNKNOWN)
        # Date
        for col in [self.HOSPITAL_DATE, self.CONFIRM_DATE, self.OUTCOME_DATE]:
            df[col] = pd.to_datetime(
                df[col], infer_datetime_format=True, errors="coerce")
        df = df.loc[~df[self.CONFIRM_DATE].isna()]
        # Outcome
        df[self.C] = ~df[self.CONFIRM_DATE].isna()
        df[self.R] = df[self.OUTCOME].str.lower().isin(
            [
                "recovered", "discharge", "discharged", "released from quarantine",
                "discharged from hospital", "not hospitalized"
            ]
        )
        df[self.F] = df[self.OUTCOME].str.lower().isin(
            ["deceased", "died", "death", "dead"]
        )
        df[self.CI] = df[[self.C, self.R, self.F]].swifter.progress_bar(False).apply(
            lambda x: x[0] and not x[1] and x[2], axis=1)
        # Symptoms
        df[self.SYMPTOM] = df[self.SYMPTOM].str.replace(", ", ":")
        # Chronic disease
        df[self.CHRONIC] = df[self.CHRONIC].str.replace(", ", ":")
        df.loc[df[self.CHRONIC].str.contains(
            "http", na=False), self.CHRONIC] = None
        # Age
        df[self.AGE] = pd.to_numeric(df[self.AGE], errors="coerce")
        # Sex
        df[self.SEX] = df[self.SEX].fillna(self.UNKNOWN)
        # Select columns
        return df.loc[:, self.LINELIST_COLS]

    def subset(self, country, province=None):
        """
        Return subset of the country/province.

        Args:
            country (str): country name or ISO3 code
            province (str or None): province name

        Returns:
            pandas.DataFrame
                Index:
                    reset index
                Columns:
                    - Hospitalized_date (pandas.TimeStamp or NT)
                    - Confirmation_date (pandas.TimeStamp or NT)
                    - Outcome_date (pandas.TimeStamp or NT)
                    - Confirmed (bool)
                    - Infected (bool)
                    - Recovered (bool)
                    - Fatal (bool)
                    - Symtoms (str)
                    - Chronic_disease (str)
                    - Age (int or None)
                    - Sex (str)
        """
        df = self._cleaned_df.copy()
        # Subset by country name
        country = self.ensure_country_name(country)
        df = df.loc[df[self.COUNTRY] == country]
        # Subset by province name
        if province not in (None, self.UNKNOWN):
            df = df.loc[df[self.PROVINCE] == province]
        # Check records are registered
        country_alias = self.ensure_country_name(country)
        if df.empty:
            raise SubsetNotFoundError(
                country=country, country_alias=country_alias, province=province)
        df = df.drop([self.COUNTRY, self.PROVINCE], axis=1)
        return df.reset_index(drop=True)

    def closed(self, outcome="Recovered"):
        """
        Return subset of global outcome data (recovered/fatal).

        Args:
            outcome (str): 'Recovered' or 'Fatal'

        Returns:
            pandas.DataFrame
                Index:
                    reset index
                Columns:
                    - Country (str): country name
                    - Province (str): province name or "-"
                    - Hospitalized_date (pandas.TimeStamp or NT)
                    - Confirmation_date (pandas.TimeStamp)
                    - Recovered_date (pandas.TimeStamp): if outcome is Recovered
                    - Fatal_date (pandas.TimeStamp): if outcome is Fatal
                    - Symptoms (str)
                    - Chronic_disease (str)
                    - Age (int or None)
                    - Sex (str)
        """
        column_dict = {self.R: self.R_DATE, self.F: self.F_DATE}
        if outcome not in column_dict:
            raise KeyError(
                f"@outcome should be selected from {self.R} or {self.F}, but {outcome} was applied.")
        df = self._cleaned_df.copy()
        df = df.loc[df[outcome]]
        # Subset by date
        df = df.loc[df[self.CONFIRM_DATE] < df[self.OUTCOME_DATE]]
        # Column names
        df = df.rename({self.OUTCOME_DATE: column_dict[outcome]}, axis=1)
        df = df.drop([self.C, self.CI, self.F, self.R], axis=1)
        return df.reset_index(drop=True)

    def recovery_period(self):
        """
        Calculate median value of recovery period (from confirmation to recovery).

        Returns:
            int: recovery period [days]
        """
        df = self.closed(outcome=self.R)
        series = (df[self.R_DATE] - df[self.CONFIRM_DATE]).dt.days
        return int(series.median())

    def total(self):
        """
        This is not defined for this child class.
        """
        raise NotImplementedError
