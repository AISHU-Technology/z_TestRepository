import React from 'react';
import { mount } from 'enzyme';
import { act, sleep } from '@/tests';
import serviceStorageManagement from '@/services/storageManagement';
import Created from '../createModal/index';

const props = {
  visible: true,
  closeModal: jest.fn(),
  optionType: 'create',
  optionStorage: Object,
  getAuthCodeType: jest.fn(),
  initData: jest.fn(),
  getData: jest.fn()
};

serviceStorageManagement.graphDBCreate = jest.fn(() => Promise.resolve({ res: 'success' }));
serviceStorageManagement.graphDBUpdate = jest.fn(() => Promise.resolve({ res: 'success' }));
serviceStorageManagement.graphDBTest = jest.fn(() => Promise.resolve({ res: 'success' }));
serviceStorageManagement.openSearchGet = jest.fn(() =>
  Promise.resolve({ res: { data: [{ id: 1, name: '内置opensearch' }] }, count: 1 })
);

const init = (props = {}) => mount(<Created {...props} />);

describe('UI test', () => {
  it('should render', async () => {
    init(props);
    await sleep();
  });
});

describe('Function test', () => {
  it('ok btn click', async () => {
    const wrapper = init(props);

    await sleep();

    act(() => {
      wrapper
        .find('.name-input')
        .at(0)
        .simulate('change', { target: { value: 'ygname' } });
      wrapper
        .find('.user-input')
        .at(0)
        .simulate('change', { target: { value: 'admin' } });
      wrapper
        .find('.pass-input')
        .at(0)
        .simulate('change', { target: { value: 'admin' } });
      wrapper
        .find('.ip-input2')
        .at(0)
        .simulate('change', { target: { value: '1.2.3.4:23' } });
    });

    await sleep();
    wrapper.update();

    act(() => {
      wrapper.find('.btn.primary').at(0).simulate('click');
    });
    await sleep();

    expect(serviceStorageManagement.graphDBCreate).toHaveBeenCalled();

    act(() => {
      wrapper.find('.ant-btn-default .btn-cancel').at(0).simulate('click');
    });
    await sleep();

    expect(serviceStorageManagement.graphDBTest).toHaveBeenCalled();
  });

  it('edit', async () => {
    const wrapper = init({ ...props, optionType: 'edit' });

    await sleep();
    act(() => {
      wrapper
        .find('.name-input')
        .at(0)
        .simulate('change', { target: { value: 'ygname' } });
      wrapper
        .find('.user-input')
        .at(0)
        .simulate('change', { target: { value: 'admin' } });
      wrapper
        .find('.pass-input')
        .at(0)
        .simulate('change', { target: { value: 'admin' } });
      wrapper
        .find('.ip-input2')
        .at(0)
        .simulate('change', { target: { value: '1.2.3.4:23' } });
    });
    await sleep();
    wrapper.update();

    act(() => {
      wrapper.find('.btn.primary').at(0).simulate('click');
    });
    await sleep();

    expect(serviceStorageManagement.graphDBUpdate).toHaveBeenCalled();
  });
});
