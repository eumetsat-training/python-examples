#!/bin/bash
#

############################################
# User Configuration
############################################

# adapt this path to your needs
gptPath="/opt/snap/bin/gpt.sh"

############################################
# Command line handling
############################################

# first parameter is a path to the graph xml
graphXmlPath="$1"

# use second parameter for path to source products
sourceDirectory="$2"

# use third parameter for path to target products
targetDirectory="$3"

# the fourth parameter is a file prefix for the target product name, typically indicating the type of processing
targetFilePrefix="$4"

   
############################################
# Helper functions
############################################

# Borrowed from http://www.linuxjournal.com/content/normalizing-path-names-bash
function normalizePath() {
    # Remove all /./ sequences.
    local path="${1//\/.\//\/}"
    
    # Remove first dir/.. sequence.
    local npath=$(echo "$path" | sed -e 's;[^/][^/]*/\.\./;;')
    
    # Remove remaining dir/.. sequence.
    while [[ "$npath" != "$path" ]]; do
        path="$npath"
        npath=$(echo "$path" | sed -e 's;[^/][^/]*/\.\./;;')
    done
    echo "$path"
}

getAbsolutePath() {
    file="$1"

    if [ "${file:0:1}" = "/" ]; then
        # already absolute
        echo "$file"
        return
    fi

    absfile="$(pwd)/${file}"
    absfile="$(normalizePath "${absfile}")"
    echo "${absfile}"
}

removeExtension() {
    file="$1"

    echo "$(echo "$file" | sed -r 's/\.[^\.]*$//')"
}


############################################
# Main processing
############################################

# Create the target directory
mkdir -p "${targetDirectory}"

IFS=$'\n'
for F in $(ls -1 "${sourceDirectory}"/S2*.SAFE); do
  sourceFile="$(getAbsolutePath "$F")"
  targetFile="${targetDirectory}/${targetFilePrefix}_$(removeExtension "${F}").dim"
  procCmd="\"${gptPath}\" \"${graphXmlPath}\" -e -p \"${parameterFilePath}\" -t \"${targetFile}\"" \"${sourceFile}\"
  "${procCmd}"
done
