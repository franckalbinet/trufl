# Release notes

<!-- do not remove -->

## 0.2.0

### Breaking Changes

- Migrate to nbdev 3 ([#3](https://github.com/franckalbinet/trufl/issues/3))

### New Features

- Document every module with docments, prose and examples ([#4](https://github.com/franckalbinet/trufl/issues/4))

### Bugs Squashed

- Normalizers ignore a whole criterion when one value is missing ([#8](https://github.com/franckalbinet/trufl/issues/8))
- `Optimizer.get_rank` requires `w_vector` even when weights can be computed ([#7](https://github.com/franckalbinet/trufl/issues/7))
- `Sampler.loc_ids` raises `AttributeError` on duplicate ids ([#6](https://github.com/franckalbinet/trufl/issues/6))
- `trufl.optimizer` imports nbdev at runtime ([#5](https://github.com/franckalbinet/trufl/issues/5))
