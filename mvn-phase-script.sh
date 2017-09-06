#!/bin/bash

# ================================================================================
# Copyright (c) 2017 AT&T Intellectual Property. All rights reserved.
# ================================================================================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============LICENSE_END=========================================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.


echo "running script: [$0] for module [$1] at stage [$2]"

MVN_PROJECT_MODULEID="$1" 
MVN_PHASE="$2"

echo "MVN_PROJECT_MODULEID is            [$MVN_PROJECT_MODULEID]"
echo "MVN_PHASE is                       [$MVN_PHASE]"
echo "MVN_PROJECT_GROUPID is             [$MVN_PROJECT_GROUPID]"
echo "MVN_PROJECT_ARTIFACTID is          [$MVN_PROJECT_ARTIFACTID]"
echo "MVN_PROJECT_VERSION is             [$MVN_PROJECT_VERSION]"
echo "MVN_NEXUSPROXY is                  [$MVN_NEXUSPROXY]"
echo "MVN_RAWREPO_BASEURL_UPLOAD is      [$MVN_RAWREPO_BASEURL_UPLOAD]"
echo "MVN_RAWREPO_BASEURL_DOWNLOAD is    [$MVN_RAWREPO_BASEURL_DOWNLOAD]"
MVN_RAWREPO_HOST=$(echo "$MVN_RAWREPO_BASEURL_UPLOAD" | cut -f3 -d'/' |cut -f1 -d':')
echo "MVN_RAWREPO_HOST is                [$MVN_RAWREPO_HOST]"
echo "MVN_RAWREPO_SERVERID is            [$MVN_RAWREPO_SERVERID]"
echo "MVN_DOCKERREGISTRY_DAILY is        [$MVN_DOCKERREGISTRY_DAILY]"
echo "MVN_DOCKERREGISTRY_RELEASE is      [$MVN_DOCKERREGISTRY_RELEASE]"

if [[ "$MVN_PROJECT_VERSION" == *SNAPSHOT ]]; then
  echo "=> for SNAPSHOT artifact build"
  MVN_DEPLOYMENT_TYPE='SNAPSHOT'
else
  echo "=> for STAGING/RELEASE artifact build"
  MVN_DEPLOYMENT_TYPE='STAGING'
fi
echo "MVN_DEPLOYMENT_TYPE is             [$DEPLOYMENT_TYPE]"


echo "=> Prepare environment "
#env

TIMESTAMP=$(date +%C%y%m%dT%H%M%S) 
export BUILD_NUMBER="${TIMESTAMP}"

# expected environment variables 
if [ -z "${MVN_NEXUSPROXY}" ]; then
    echo "MVN_NEXUSPROXY environment variable not set.  Cannot proceed"
    exit
fi

MVN_NEXUSPROXY_HOST=$(echo "$MVN_NEXUSPROXY" |cut -f3 -d'/' | cut -f1 -d':')
echo "=> Nexus Proxy at $MVN_NEXUSPROXY_HOST, $MVN_NEXUSPROXY"

if [ -z "$WORKSPACE" ]; then
    WORKSPACE=$(pwd)
fi

# mvn phase in life cycle 
MVN_PHASE="$2"

case $MVN_PHASE in
clean)
  echo "==> clean phase script"
  rm -rf ./venv-tox
  ;;
generate-sources)
  echo "==> generate-sources phase script"
  ;;
compile)
  echo "==> compile phase script"
  ;;
test)
  echo "==> test phase script"
  virtualenv ./venv-tox
  source ./venv-tox/bin/activate
  pip install --upgrade pip
  pip install --upgrade tox argparse
  pip freeze
  cd $WORKSPACE/ 
  tox
  deactivate
  echo "==> test phase script done"
  ;;
package)
  echo "==> package phase script"
  ;;
install)
  echo "==> install phase script"
  ;;
deploy)
  echo "==> deploy phase script"

  FQDN="${MVN_PROJECT_GROUPID}.${MVN_PROJECT_ARTIFACTID}"
  if [ "$MVN_PROJECT_MODULEID" == "__" ]; then
    MVN_PROJECT_MODULEID=""
  fi

if false; then
  # ============================= example deploying raw artifact ===========================
  # Extract the username and password to the nexus repo from the settings file
  USER=$(xpath -q -e "//servers/server[id='$MVN_RAWREPO_SERVERID']/username/text()" "$SETTINGS_FILE")
  PASS=$(xpath -q -e "//servers/server[id='$MVN_RAWREPO_SERVERID']/password/text()" "$SETTINGS_FILE")
  NETRC=$(mktemp)
  echo "machine $MVN_RAWREPO_HOST login $USER password $PASS" > "$NETRC"

  REPO="$MVN_RAWREPO_BASEURL_DOWNLOAD"
  FQDN="${MVN_PROJECT_GROUPID}.${MVN_PROJECT_ARTIFACTID}"


  OUTPUT_FILE='analytics.bin'
  echo "Test" > ${OUTPUT_FILE}

  SEND_TO="${REPO}/${FQDN}/todelete/${OUTPUT_FILE}"
  echo "Sending ${OUTPUT_FILE} to Nexus: ${SEND_TO}"
  curl -vkn --netrc-file "${NETRC}" --upload-file "${OUTPUT_FILE}" "${SEND_TO}"
  # ========================== end of example deploying raw artifact ========================
fi 


  # ================== example building and deploying docker image ==========================
  IMAGENAME="onap/${FQDN}.${MVN_PROJECT_MODULEID}"
  IMAGENAME=$(echo "$IMAGENAME" | sed -e 's/_*$//g' -e 's/\.*$//g')

  # use the major and minor version of the MVN artifact version as docker image version
  VERSION="${MVN_PROJECT_VERSION//[^0-9.]/}"
  VERSION2=$(echo "$VERSION" | cut -f1-2 -d'.')
   
  LFQI="${IMAGENAME}:${VERSION}-${TIMESTAMP}"
  BUILD_PATH="${WORKSPACE}"
  # build a docker image
  docker build --rm -f "${WORKSPACE}"/Dockerfile -t "${LFQI}" "${BUILD_PATH}"

  REPO="" 
  if [ $MVN_DEPLOYMENT_TYPE == "SNAPSHOT" ]; then
     REPO=$MVN_DOCKERREGISTRY_DAILY
  elif [ $MVN_DEPLOYMENT_TYPE == "STAGING" ]; then
     REPO=$MVN_DOCKERREGISTRY_RELEASE
  else 
     echo "Fail to determine DEPLOYMENT_TYPE"
     REPO=$MVN_DOCKERREGISTRY_DAILY
  fi
  echo "DEPLOYMENT_TYPE is: $MVN_DEPLOYMENT_TYPE, repo is $REPO"

  if [ ! -z "$REPO" ]; then 
    USER=$(xpath -e "//servers/server[id='$REPO']/username/text()" "$SETTINGS_FILE")
    PASS=$(xpath -e "//servers/server[id='$REPO']/password/text()" "$SETTINGS_FILE")
    if [ -z "$USER" ]; then
      echo "Error: no user provided"
    fi
    if [ -z "$PASS" ]; then
      echo "Error: no password provided"
    fi
    [ -z "$PASS" ] && PASS_PROVIDED="<empty>" || PASS_PROVIDED="<password>"
    echo docker login "$REPO" -u "$USER" -p "$PASS_PROVIDED"
    docker login "$REPO" -u "$USER" -p "$PASS"

    OLDTAG="${LFQI}"
    PUSHTAGS="${REPO}/${IMAGENAME}:${VERSION2}-${TIMESTAMP} ${REPO}/${IMAGENAME}:${VERSION2} ${REPO}/${IMAGENAME}:${VERSION2}-latest"
    for NEWTAG in ${PUSHTAGS}
    do
      echo "tagging ${OLDTAG} to ${NEWTAG}" 
      docker tag "${OLDTAG}" "${NEWTAG}"
      echo "pushing ${NEWTAG}" 
      docker push "${NEWTAG}"
      OLDTAG="${NEWTAG}"
    done
  fi
 
  # ============= end of example building and deploying docker image ========================
  ;;
*)
  echo "==> unprocessed phase"
  ;;
esac

