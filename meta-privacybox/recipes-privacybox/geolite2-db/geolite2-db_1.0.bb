SUMMARY = "GeoLite2 Country Database (MaxMind)"
DESCRIPTION = "Free IP geolocation database for country-level lookups"
LICENSE = "CC-BY-SA-4.0"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/CC-BY-SA-4.0;md5=fba3b94d88bfb9b81369d69a0cc7d80a"

# Download GeoLite2-Country database during build
# Free database from MaxMind via GitHub mirror
# Source: https://github.com/P3TERX/GeoLite.mmdb
DB_URL = "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb"
DB_FILENAME = "GeoLite2-Country.mmdb"

SRC_URI = " \
    ${DB_URL};name=db;downloadfilename=${DB_FILENAME} \
"

# Skip checksum verification - database updates frequently
SRC_URI[db.sha256sum] = "skip"
SRC_URI[db.md5sum] = "skip"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${datadir}/device-tracker
    install -d ${D}${sysconfdir}/device-tracker
    
    # Install database file
    if [ -f "${WORKDIR}/${DB_FILENAME}" ]; then
        install -m 0644 ${WORKDIR}/${DB_FILENAME} ${D}${datadir}/device-tracker/
        install -m 0644 ${WORKDIR}/${DB_FILENAME} ${D}${sysconfdir}/device-tracker/
    else
        bbwarn "GeoLite2 database file not found. Download may have failed."
    fi
}

FILES:${PN} += " \
    ${datadir}/device-tracker/${DB_FILENAME} \
    ${sysconfdir}/device-tracker/${DB_FILENAME} \
"

