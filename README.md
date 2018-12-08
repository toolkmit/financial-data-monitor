# Financial Data Monitor

I've put together this project because I have difficulty
staying on top of trends in the financial
markets.  This will constantly be a work in progress, but
over time the project will cover the futures, forex, and 
stock markets globally in addition to economic data.

The current iteration of the project loads CME futures data
from Quandl, charts the data on different timeframes, and
can send an email with a pdf of the charts.

## Getting Started

The project is designed to be run in a Docker container
which can be deployed on your local machine or run in the
cloud on a service such as Amazon ECS with S3 storage.

I find it easy to use Amazon Fargate to spin up a container
to update the futures data and send an email with the new
charts.

### Prerequisites

Docker and git will need to be installed on your local
machine.  To upload to AWS, you will also need to install
the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)

### Installing

To install, clone the git repository and build the Docker
image.

```
git clone https://github.com/toolkmit/financial-data-monitor.git
docker build -t financial-data-monitor .
```

To deploy on ECS/Fargate, you first need to set up an S3
bucket with the name financial-data-monitor, then build the
Docker image from git source and then upload to the Elastic
Container registry.

```
$(aws ecr get-login --no-include-email --region us-east-1)
docker build -t fdm https://github.com/toolkmit/financial-data-monitor.git
docker tag fdm:latest 096908083292.dkr.ecr.us-east-1.amazonaws.com/fdm:latest
docker push 096908083292.dkr.ecr.us-east-1.amazonaws.com/fdm:latest
```

Once the image is in the Elastic Container Registry, you
need to setup your Fargate cluster and task definition.
I'll add more on how to do this in a bit, but below are 2
resources that I used to get started:

* [How to deploy a Docker app to Amazon ECS using AWS Fargate](https://read.acloud.guru/deploy-the-voting-app-to-aws-ecs-with-fargate-cb75f226408f)
* [Run tasks with AWS Fargate and Lambda](https://lobster1234.github.io/2017/12/03/run-tasks-with-aws-fargate-and-lambda/)
