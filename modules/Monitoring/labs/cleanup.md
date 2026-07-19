```

eksctl delete cluster --name monitoring-lab --region us-east-1


# Delete the leftover CloudFormation stacks
aws cloudformation delete-stack \
  --region us-east-1 \
  --stack-name eksctl-monitoring-lab-cluster

# Wait for deletion to complete (may take 5-10 minutes)
aws cloudformation wait stack-delete-complete \
  --region us-east-1 \
  --stack-name eksctl-monitoring-lab-cluster

# Also delete the nodegroup stack if it exists
aws cloudformation delete-stack \
  --region us-east-1 \
  --stack-name eksctl-monitoring-lab-nodegroup-ng-1
```

Then go in AWS and delete any Load Balancers under ec2 in same region.