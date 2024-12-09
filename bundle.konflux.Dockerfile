FROM brew.registry.redhat.io/rh-osbs/openshift-golang-builder:rhel_9_1.22 as builder

ARG IMG=registry.redhat.io/nbde-tang-server/nbde-tang-server-rhel9-operator@sha256:17ff5bd2ff62569f38a065a64762ce7beb0046d975faae03836b3f6c3cca3596
ARG ORIGINAL_IMG=quay.io/sec-eng-special/nbde-tang-server:v1.1.0
WORKDIR /code
COPY ./ ./

# Replace the bundle image in the repository with the one specified by the IMG build argument.
RUN chmod -R g+rwX ./ && find bundle/ && find bundle -type f -exec sed -i \
   "s|${ORIGINAL_IMG}|${IMG})|g" {} \+; grep -rq "${ORIGINAL_IMG}" bundle/ && \
   { echo "Failed to replace image references"; exit 1; } || echo "Image references replaced" && \
   grep -r "${IMG}" bundle/

FROM registry.access.redhat.com/ubi9/ubi-micro@sha256:a410623c2b8e9429f9606af821be0231fef2372bd0f5f853fbe9743a0ddf7b34

# Include required labels (for Konflux deployment)
LABEL com.redhat.component="NBDE Tang Server (Bundle)"
LABEL distribution-scope="public"
LABEL name="nbde-tang-server-bundle"
LABEL release="1.1.0"
LABEL version="1.1.0"
LABEL url="https://github.com/openshift/nbde-tang-server"
LABEL vendor="Red Hat, Inc."
LABEL description="The NBDE Tang Server operator allows NBDE technology deployment on OpenShift"
LABEL io.k8s.description="The NBDE Tang Server Operator allows NBDE technology deployment on OpenShift"
LABEL summary="The NBDE Tang Server operator allows NBDE technology deployment on OpenShift"
LABEL io.k8s.display-name="NBDE Tang Server"
LABEL io.openshift.tags="openshift,operator,nbde,network,security,storage,disk,unlocking"

# Include referenced image so that it can be easily verified in the bundle
LABEL konflux.referenced.image="registry.redhat.io/nbde-tang-server/nbde-tang-server-rhel9-operator@sha256:17ff5bd2ff62569f38a065a64762ce7beb0046d975faae03836b3f6c3cca3596"

# Core bundle labels.
LABEL operators.operatorframework.io.bundle.mediatype.v1=registry+v1
LABEL operators.operatorframework.io.bundle.manifests.v1=manifests/
LABEL operators.operatorframework.io.bundle.metadata.v1=metadata/
LABEL operators.operatorframework.io.bundle.package.v1=nbde-tang-server
LABEL operators.operatorframework.io.bundle.channels.v1=stable
LABEL operators.operatorframework.io.metrics.builder=operator-sdk-v1.37.0
LABEL operators.operatorframework.io.metrics.mediatype.v1=metrics+v1
LABEL operators.operatorframework.io.metrics.project_layout=go.kubebuilder.io/v4

# Labels for testing.
LABEL operators.operatorframework.io.test.mediatype.v1=scorecard+v1
LABEL operators.operatorframework.io.test.config.v1=tests/scorecard/

### Copy files to locations specified by labels
COPY --from=builder /code/bundle/manifests /manifests/
COPY --from=builder /code/bundle/metadata /metadata/
COPY --from=builder /code/bundle/tests/scorecard /tests/scorecard/

# Copy LICENSE to /licenses directory
COPY LICENSE /licenses/
