#!/bin/sh
java -jar -Dspring.profiles.active=$1 /app/application.jar
