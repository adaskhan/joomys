from .tasks import HHKZVacancyScrapper, HHKZVacancyChecker, BeamKzVacancyScrapper

START_HOUR = 10
START_MINUTE = 1
ALL_SCRAPPERS = [
    HHKZVacancyScrapper("Qa", "hh.kz qa", hour=START_HOUR, minute=START_MINUTE+2),
    HHKZVacancyScrapper("Product Manager", "hh.kz product manager", hour=START_HOUR, minute=START_MINUTE+4),
    HHKZVacancyScrapper("Devops", "hh.kz devops", hour=START_HOUR, minute=START_MINUTE+6),
    HHKZVacancyScrapper("Data analyst", "hh.kz data analyst", hour=START_HOUR, minute=START_MINUTE+8),
    HHKZVacancyScrapper("Data scientist", "hh.kz data scientist", hour=START_HOUR, minute=START_MINUTE+10),
    HHKZVacancyScrapper("programmist", "hh.kz programmer", hour=START_HOUR, minute=START_MINUTE+12),
    HHKZVacancyScrapper("dizajner-interfejsov", "hh.kz designer", hour=START_HOUR, minute=START_MINUTE+14),
    HHKZVacancyScrapper("sistemnyy_administrator", "hh.kz sysadmin", hour=START_HOUR, minute=START_MINUTE+16),
    BeamKzVacancyScrapper("программист", "beam.kz programmer", hour=START_HOUR, minute=START_MINUTE+16),
    BeamKzVacancyScrapper("дизайнер", "beam.kz designer", hour=START_HOUR, minute=START_MINUTE+16),
    BeamKzVacancyScrapper("проект менеджер", "beam.kz project manager", hour=START_HOUR, minute=START_MINUTE+16),
]


ALL_CHECKERS = [
                    HHKZVacancyChecker()
]