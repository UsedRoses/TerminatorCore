_consumer_list = {}
def _register_consumer(sub_cls):
    name = sub_cls.__name__
    if name not in _consumer_list:
        _consumer_list[name] = sub_cls
        print(f"Registered consumer: {name}")


def consumer_start():
    open_dead = False
    # 启动所有消费者
    for key, consumer_class in _consumer_list.items():
        if key == 'DeadConsumer':
            continue
        consumer_instance = consumer_class()
        consumer_instance.consume()
        open_dead = True

    if open_dead:
        dead_consumer_class = _consumer_list.get('DeadConsumer')
        if dead_consumer_class:
            dead_consumer_class().consume()
