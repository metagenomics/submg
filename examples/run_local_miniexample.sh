set -e

LOCAL=localtest.yaml
STAGING_DIR=localtest/staging
LOGGING_DIR=localtest/logging
rm -rf $STAGING_DIR $LOGGING_DIR


CFG=07_assembly_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-assembly \
--submit-bins \
--submit-mags
rm -rf $STAGING_DIR $LOGGING_DIR


echo ""
echo "##################################################################"
echo "##################################################################"
echo "All examples submitted"
echo "##################################################################"
echo "##################################################################"