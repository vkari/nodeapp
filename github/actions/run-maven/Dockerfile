FROM alpine:latest
ARG JAR_FILE
ARG BUILD_ENV
ENV BUILD_ENVS=${BUILD_ENV}
USER root
RUN apk update
RUN apk add bind-tools net-tools curl openjdk21 ca-certificates

#VOLUME /tmp
#RUN mkdir -p /app
#RUN chmod -R 755 /app
# COPY pipeline/docker/okta-com-chain.pem /usr/local/share/ca-certificates/okta-com-chain.pem
# RUN update-ca-certificates
#COPY target/${JAR_FILE} /app/application.jar
#COPY src/main/resources/${BUILD_ENV}.properties /app/application.properties

WORKDIR /app
COPY ./okta-com-chain.pem ./okta-com-chain.pem
#COPY ./json ./src/main/resources/
COPY ./application.jar ./application.jar
# RUN keytool -importcert -file /usr/local/share//ca-certificates/okta-com-chain.pem -keystore /etc/ssl/certs/java/cacerts -storepass changeit -noprompt -alias tsc-chain
#COPY ./app /app
#COPY devops/docker/productgraphqlapiApp/commands.sh /app/commands.sh
RUN chmod -R 755 .

#RUN ["chmod", "+x", "/app/commands.sh"]
# ENTRYPOINT ["java","-jar","-Dspring.config.location=file:/config/application.properties /storelocator-0.0.1-SNAPSHOT.jar"]
#ENTRYPOINT java -jar -Dspring.profiles.active=d1 /app/application.jar
ENTRYPOINT ["java", "-jar", "-Dspring.profiles.active=${ENVIRONMENT}", "-Dsun.misc.URLClassPath.disableJarChecking=true", "-XX:+UnlockExperimentalVMOptions", "-XX:MinRAMPercentage=20.0", "-XX:MaxRAMPercentage=70.0", "-XX:+UseG1GC", "-XX:+UseStringDeduplication", "-XX:StringDeduplicationAgeThreshold=6", "-XX:G1ReservePercent=10", "-XX:NewRatio=3", "./application.jar"]
