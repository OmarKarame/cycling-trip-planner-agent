from src.models import VisaInput, VisaOutput, VisaRequirement

# Simplified EU/Schengen + common cycling destinations
_EU_SCHENGEN = {
    "netherlands", "germany", "denmark", "france", "belgium", "luxembourg",
    "austria", "czech republic", "czechia", "poland", "italy", "spain",
    "portugal", "sweden", "norway", "switzerland", "hungary", "croatia",
    "slovenia", "slovakia", "greece", "finland", "estonia", "latvia",
    "lithuania", "iceland", "liechtenstein", "malta", "cyprus", "romania",
    "bulgaria",
}

_EU_NATIONALITIES = {
    "dutch", "german", "danish", "french", "belgian", "italian", "spanish",
    "portuguese", "swedish", "norwegian", "swiss", "austrian", "czech",
    "polish", "hungarian", "croatian", "slovenian", "greek", "finnish",
    "estonian", "latvian", "lithuanian", "irish", "british", "american",
    "canadian", "australian", "japanese", "south korean",
}

# Countries that typically need visas for non-EU nationals
_VISA_REQUIRED_FOR_NON_EU = {"turkey", "russia", "china", "india", "vietnam"}


class MockVisaProvider:
    """Mock visa provider with simplified EU/Schengen rules."""

    def check_visa_requirements(self, input: VisaInput) -> VisaOutput:
        nationality = input.nationality.lower().strip()
        requirements = []

        for country in input.countries:
            country_lower = country.lower().strip()

            if country_lower in _EU_SCHENGEN:
                if nationality in _EU_NATIONALITIES:
                    requirements.append(
                        VisaRequirement(
                            country=country,
                            visa_required=False,
                            notes="No visa required. Free movement within the EU/Schengen area.",
                        )
                    )
                else:
                    requirements.append(
                        VisaRequirement(
                            country=country,
                            visa_required=False,
                            visa_type="Schengen visa-free",
                            notes=(
                                "Most nationalities can enter Schengen zone visa-free "
                                "for up to 90 days. Check your specific nationality's rules."
                            ),
                        )
                    )
            elif country_lower in _VISA_REQUIRED_FOR_NON_EU:
                requirements.append(
                    VisaRequirement(
                        country=country,
                        visa_required=True,
                        visa_type="Tourist visa",
                        notes="Tourist visa required. Apply at least 4 weeks before travel.",
                    )
                )
            else:
                requirements.append(
                    VisaRequirement(
                        country=country,
                        visa_required=False,
                        notes="No visa typically required for short tourist visits.",
                    )
                )

        return VisaOutput(nationality=input.nationality, requirements=requirements)
