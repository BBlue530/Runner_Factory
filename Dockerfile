FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y git && \
    yum clean all

COPY src/ ${LAMBDA_TASK_ROOT}/

COPY wheelhouse /wheelhouse

# Use this if there is no wheelhouse you can use for the dependencies
#RUN pip install --upgrade pip \
#    && pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

RUN pip install --upgrade pip && \
    pip install \
      --no-index \
      --find-links=/wheelhouse \
      --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

CMD ["lambda_handler.lambda_handler"]