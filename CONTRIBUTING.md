# Contributing to AWS Glue Data Lineage

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or request features
- Search existing issues before creating a new one
- Provide detailed information:
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (AWS region, Glue version, etc.)
  - Error messages and logs

### Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed
4. **Test your changes**
   - Deploy to a test AWS account
   - Verify lineage tracking works
   - Check CloudFormation templates validate
5. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**
   - Describe your changes
   - Reference related issues
   - Include screenshots if applicable
  
## Development Guidelines

### Code Style

**Python (Glue Jobs)**:
- Follow PEP 8
- Use meaningful variable names
- Add docstrings for functions
- Handle exceptions gracefully

**CloudFormation**:
- Use descriptive resource names
- Add descriptions to parameters
- Include outputs for important values
- Use !Sub for string interpolation

### Testing

Before submitting:
- [ ] CloudFormation templates validate
- [ ] Glue jobs run successfully
- [ ] Lineage events appear in Marquez
- [ ] Documentation is updated
- [ ] No sensitive data in code

### Documentation

Update documentation when:
- Adding new features
- Changing architecture
- Modifying configuration
- Adding dependencies

## Areas for Contribution

### High Priority

- [ ] Add support for more data sources (Redshift, DynamoDB)
- [ ] Implement column-level lineage
- [ ] Add data quality facets
- [ ] Create Terraform version of templates
- [ ] Add CI/CD pipeline examples

### Medium Priority
- [ ] Add more Glue job examples
- [ ] Improve error handling
- [ ] Add monitoring dashboards
- [ ] Create troubleshooting guide
- [ ] Add unit tests

### Low Priority
- [ ] Add support for other lineage backends
- [ ] Create Helm charts for Kubernetes
- [ ] Add performance benchmarks
- [ ] Create video tutorials

## Questions?

- Open a GitHub Discussion
- Check existing documentation
- Review closed issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
                                                                                             

