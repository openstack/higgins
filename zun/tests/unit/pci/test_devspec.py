#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from unittest import mock

from zun.common import exception
from zun.pci import devspec
from zun.tests import base

dev = {"vendor_id": "8086",
       "product_id": "5057",
       "address": "0000:0a:00.5",
       "parent_addr": "0000:0a:00.0"}


class PciAddressSpecTestCase(base.TestCase):
    def test_pci_address_spec_abstact_instance_fail(self):
        self.assertRaises(TypeError, devspec.PciAddressSpec)


class PhysicalPciAddressTestCase(base.TestCase):
    pci_addr = {"domain": "0000",
                "bus": "0a",
                "slot": "00",
                "function": "5"}

    def test_init_by_dict(self):
        phys_addr = devspec.PhysicalPciAddress(self.pci_addr)
        self.assertEqual(phys_addr.domain, self.pci_addr['domain'])
        self.assertEqual(phys_addr.bus, self.pci_addr['bus'])
        self.assertEqual(phys_addr.slot, self.pci_addr['slot'])
        self.assertEqual(phys_addr.func, self.pci_addr['function'])

    def test_init_by_dict_invalid_address_values(self):
        invalid_val_addr = {"domain": devspec.MAX_DOMAIN + 1,
                            "bus": devspec.MAX_BUS + 1,
                            "slot": devspec.MAX_SLOT + 1,
                            "function": devspec.MAX_FUNC + 1}
        for component in invalid_val_addr:
            address = dict(self.pci_addr)
            address[component] = str(invalid_val_addr[component])
            self.assertRaises(exception.PciConfigInvalidWhitelist,
                              devspec.PhysicalPciAddress, address)

    def test_init_by_dict_missing_values(self):
        for component in self.pci_addr:
            address = dict(self.pci_addr)
            del address[component]
            self.assertRaises(exception.PciDeviceWrongAddressFormat,
                              devspec.PhysicalPciAddress, address)

    def test_init_by_string(self):
        address_str = "0000:0a:00.5"
        phys_addr = devspec.PhysicalPciAddress(address_str)
        self.assertEqual(phys_addr.domain, "0000")
        self.assertEqual(phys_addr.bus, "0a")
        self.assertEqual(phys_addr.slot, "00")
        self.assertEqual(phys_addr.func, "5")

    def test_init_by_string_invalid_values(self):
        invalid_addresses = [str(devspec.MAX_DOMAIN + 1) + ":0a:00.5",
                             "0000:" + str(devspec.MAX_BUS + 1) + ":00.5",
                             "0000:0a:" + str(devspec.MAX_SLOT + 1) + ".5",
                             "0000:0a:00." + str(devspec.MAX_FUNC + 1)]
        for address in invalid_addresses:
            self.assertRaises(exception.PciConfigInvalidWhitelist,
                              devspec.PhysicalPciAddress, address)

    def test_init_by_string_missing_values(self):
        invalid_addresses = ["00:0000:0a:00.5", "0a:00.5", "0000:00.5"]
        for address in invalid_addresses:
            self.assertRaises(exception.PciDeviceWrongAddressFormat,
                              devspec.PhysicalPciAddress, address)

    def test_match(self):
        address_str = "0000:0a:00.5"
        phys_addr1 = devspec.PhysicalPciAddress(address_str)
        phys_addr2 = devspec.PhysicalPciAddress(address_str)
        self.assertTrue(phys_addr1.match(phys_addr2))

    def test_false_match(self):
        address_str = "0000:0a:00.5"
        phys_addr1 = devspec.PhysicalPciAddress(address_str)
        addresses = ["0010:0a:00.5", "0000:0b:00.5",
                     "0000:0a:01.5", "0000:0a:00.4"]
        for address in addresses:
            phys_addr2 = devspec.PhysicalPciAddress(address)
            self.assertFalse(phys_addr1.match(phys_addr2))


class PciAddressGlobSpecTestCase(base.TestCase):
    def test_init(self):
        address_str = "0000:0a:00.5"
        phys_addr = devspec.PciAddressGlobSpec(address_str)
        self.assertEqual(phys_addr.domain, "0000")
        self.assertEqual(phys_addr.bus, "0a")
        self.assertEqual(phys_addr.slot, "00")
        self.assertEqual(phys_addr.func, "5")

    def test_init_invalid_address(self):
        invalid_addresses = ["00:0000:0a:00.5"]
        for address in invalid_addresses:
            self.assertRaises(exception.PciDeviceWrongAddressFormat,
                              devspec.PciAddressGlobSpec, address)

    def test_init_invalid_values(self):
        invalid_addresses = [str(devspec.MAX_DOMAIN + 1) + ":0a:00.5",
                             "0000:" + str(devspec.MAX_BUS + 1) + ":00.5",
                             "0000:0a:" + str(devspec.MAX_SLOT + 1) + ".5",
                             "0000:0a:00." + str(devspec.MAX_FUNC + 1)]
        for address in invalid_addresses:
            self.assertRaises(exception.PciConfigInvalidWhitelist,
                              devspec.PciAddressGlobSpec, address)

    def test_match(self):
        address_str = "0000:0a:00.5"
        phys_addr = devspec.PhysicalPciAddress(address_str)
        addresses = ["0000:0a:00.5", "*:0a:00.5", "0000:*:00.5",
                     "0000:0a:*.5", "0000:0a:00.*"]
        for address in addresses:
            glob_addr = devspec.PciAddressGlobSpec(address)
            self.assertTrue(glob_addr.match(phys_addr))

    def test_false_match(self):
        address_str = "0000:0a:00.5"
        phys_addr = devspec.PhysicalPciAddress(address_str)
        addresses = ["0010:0a:00.5", "0000:0b:00.5",
                     "*:0a:01.5", "0000:0a:*.4"]
        for address in addresses:
            glob_addr = devspec.PciAddressGlobSpec(address)
            self.assertFalse(phys_addr.match(glob_addr))


class PciAddressRegexSpecTestCase(base.TestCase):
    def test_init(self):
        address_regex = {"domain": ".*",
                         "bus": "02",
                         "slot": "01",
                         "function": "[0-2]"}
        phys_addr = devspec.PciAddressRegexSpec(address_regex)
        self.assertEqual(phys_addr.domain, ".*")
        self.assertEqual(phys_addr.bus, "02")
        self.assertEqual(phys_addr.slot, "01")
        self.assertEqual(phys_addr.func, "[0-2]")

    def test_init_invalid_address(self):
        invalid_addresses = [{"domain": "*",
                              "bus": "02",
                              "slot": "01",
                              "function": "[0-2]"}]

        for address in invalid_addresses:
            self.assertRaises(exception.PciDeviceWrongAddressFormat,
                              devspec.PciAddressRegexSpec, address)

    def test_match(self):
        address_str = "0000:0a:00.5"
        phys_addr = devspec.PhysicalPciAddress(address_str)
        addresses = [{"domain": ".*", "bus": "0a",
                      "slot": "00", "function": "[5-6]"},
                     {"domain": ".*", "bus": "0a",
                      "slot": ".*", "function": "[4-5]"},
                     {"domain": ".*", "bus": "0a",
                      "slot": "[0-3]", "function": ".*"}]
        for address in addresses:
            regex_addr = devspec.PciAddressRegexSpec(address)
            self.assertTrue(regex_addr.match(phys_addr))

    def test_false_match(self):
        address_str = "0000:0b:00.5"
        phys_addr = devspec.PhysicalPciAddress(address_str)
        addresses = [{"domain": ".*", "bus": "0a",
                      "slot": "00", "function": "[5-6]"},
                     {"domain": ".*", "bus": "02",
                      "slot": ".*", "function": "[4-5]"},
                     {"domain": ".*", "bus": "02",
                      "slot": "[0-3]", "function": ".*"}]
        for address in addresses:
            regex_addr = devspec.PciAddressRegexSpec(address)
            self.assertFalse(regex_addr.match(phys_addr))


class PciAddressTestCase(base.TestCase):
    def test_wrong_address(self):
        pci_info = {"vendor_id": "8086", "address": "*: *: *.6",
                    "product_id": "5057", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertFalse(pci.match(dev))

    def test_address_too_big(self):
        pci_info = {"address": "0000:0a:0b:00.5",
                    "physical_network": "hr_net"}
        self.assertRaises(exception.PciDeviceWrongAddressFormat,
                          devspec.PciDeviceSpec, pci_info)

    def test_address_invalid_character(self):
        pci_info = {"address": "0000:h4.12:6", "physical_network": "hr_net"}
        exc = self.assertRaises(exception.PciConfigInvalidWhitelist,
                                devspec.PciDeviceSpec, pci_info)
        msg = ('Invalid PCI devices Whitelist config invalid func 12:6')
        self.assertEqual(msg, str(exc))

    def test_max_func(self):
        pci_info = {"address": "0000:0a:00.%s" % (devspec.MAX_FUNC + 1),
                    "physical_network": "hr_net"}
        exc = self.assertRaises(exception.PciConfigInvalidWhitelist,
                                devspec.PciDeviceSpec, pci_info)
        msg = ('Invalid PCI devices Whitelist config invalid func %x'
               % (devspec.MAX_FUNC + 1))
        self.assertEqual(msg, str(exc))

    def test_max_domain(self):
        pci_info = {"address": "%x:0a:00.5" % (devspec.MAX_DOMAIN + 1),
                    "physical_network": "hr_net"}
        exc = self.assertRaises(exception.PciConfigInvalidWhitelist,
                                devspec.PciDeviceSpec, pci_info)
        msg = ('Invalid PCI devices Whitelist config invalid domain %x'
               % (devspec.MAX_DOMAIN + 1))
        self.assertEqual(msg, str(exc))

    def test_max_bus(self):
        pci_info = {"address": "0000:%x:00.5" % (devspec.MAX_BUS + 1),
                    "physical_network": "hr_net"}
        exc = self.assertRaises(exception.PciConfigInvalidWhitelist,
                                devspec.PciDeviceSpec, pci_info)
        msg = ('Invalid PCI devices Whitelist config invalid bus %x'
               % (devspec.MAX_BUS + 1))
        self.assertEqual(msg, str(exc))

    def test_max_slot(self):
        pci_info = {"address": "0000:0a:%x.5" % (devspec.MAX_SLOT + 1),
                    "physical_network": "hr_net"}
        exc = self.assertRaises(exception.PciConfigInvalidWhitelist,
                                devspec.PciDeviceSpec, pci_info)
        msg = ('Invalid PCI devices Whitelist config invalid slot %x'
               % (devspec.MAX_SLOT + 1))
        self.assertEqual(msg, str(exc))

    def test_address_is_undefined(self):
        pci_info = {"vendor_id": "8086", "product_id": "5057"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(dev))

    def test_partial_address(self):
        pci_info = {"address": ":0a:00.", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        dev = {"vendor_id": "1137",
               "product_id": "0071",
               "address": "0000:0a:00.5",
               "parent_addr": "0000:0a:00.0"}
        self.assertTrue(pci.match(dev))

    def test_partial_address_func(self):
        pci_info = {"address": ".5", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        dev = {"vendor_id": "1137",
               "product_id": "0071",
               "address": "0000:0a:00.5",
               "phys_function": "0000:0a:00.0"}
        self.assertTrue(pci.match(dev))

    @mock.patch('zun.pci.utils.is_physical_function', return_value=True)
    def test_address_is_pf(self, mock_is_physical_function):
        pci_info = {"address": "0000:0a:00.0", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(dev))

    @mock.patch('zun.pci.utils.is_physical_function', return_value=True)
    def test_address_pf_no_parent_addr(self, mock_is_physical_function):
        _dev = dev.copy()
        _dev.pop('parent_addr')
        pci_info = {"address": "0000:0a:00.5", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(_dev))

    def test_spec_regex_match(self):
        pci_info = {"address": {"domain": ".*",
                                "bus": ".*",
                                "slot": "00",
                                "function": "[5-6]"
                                },
                    "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(dev))

    def test_spec_regex_no_match(self):
        pci_info = {"address": {"domain": ".*",
                                "bus": ".*",
                                "slot": "00",
                                "function": "[6-7]"
                                },
                    "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertFalse(pci.match(dev))

    def test_spec_invalid_regex(self):
        pci_info = {"address": {"domain": ".*",
                                "bus": ".*",
                                "slot": "00",
                                "function": "[6[-7]"
                                },
                    "physical_network": "hr_net"}
        self.assertRaises(exception.PciDeviceWrongAddressFormat,
                          devspec.PciDeviceSpec, pci_info)

    def test_spec_invalid_regex2(self):
        pci_info = {"address": {"domain": "*",
                                "bus": "*",
                                "slot": "00",
                                "function": "[6-7]"
                                },
                    "physical_network": "hr_net"}
        self.assertRaises(exception.PciDeviceWrongAddressFormat,
                          devspec.PciDeviceSpec, pci_info)

    def test_spec_partial_bus_regex(self):
        pci_info = {"address": {"domain": ".*",
                                "slot": "00",
                                "function": "[5-6]"
                                },
                    "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(dev))

    def test_spec_partial_address_regex(self):
        pci_info = {"address": {"domain": ".*",
                                "bus": ".*",
                                "slot": "00",
                                },
                    "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(dev))

    def test_spec_invalid_address(self):
        pci_info = {"address": [".*", ".*", "00", "[6-7]"],
                    "physical_network": "hr_net"}
        self.assertRaises(exception.PciDeviceWrongAddressFormat,
                          devspec.PciDeviceSpec, pci_info)

    @mock.patch('zun.pci.utils.is_physical_function', return_value=True)
    def test_address_is_pf_regex(self, mock_is_physical_function):
        pci_info = {"address": {"domain": "0000",
                                "bus": "0a",
                                "slot": "00",
                                "function": "0"
                                },
                    "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(dev))


class PciDevSpecTestCase(base.TestCase):
    def test_spec_match(self):
        pci_info = {"vendor_id": "8086", "address": "*: *: *.5",
                    "product_id": "5057", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(dev))

    def test_invalid_vendor_id(self):
        pci_info = {"vendor_id": "8087", "address": "*: *: *.5",
                    "product_id": "5057", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertFalse(pci.match(dev))

    def test_vendor_id_out_of_range(self):
        pci_info = {"vendor_id": "80860", "address": "*:*:*.5",
                    "product_id": "5057", "physical_network": "hr_net"}
        exc = self.assertRaises(exception.PciConfigInvalidWhitelist,
                                devspec.PciDeviceSpec, pci_info)
        self.assertEqual("Invalid PCI devices Whitelist config "
                         "invalid vendor_id 80860", str(exc))

    def test_invalid_product_id(self):
        pci_info = {"vendor_id": "8086", "address": "*: *: *.5",
                    "product_id": "5056", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertFalse(pci.match(dev))

    def test_product_id_out_of_range(self):
        pci_info = {"vendor_id": "8086", "address": "*:*:*.5",
                    "product_id": "50570", "physical_network": "hr_net"}
        exc = self.assertRaises(exception.PciConfigInvalidWhitelist,
                                devspec.PciDeviceSpec, pci_info)
        self.assertEqual("Invalid PCI devices Whitelist config "
                         "invalid product_id 50570", str(exc))

    def test_devname_and_address(self):
        pci_info = {"devname": "eth0", "vendor_id": "8086",
                    "address": "*:*:*.5", "physical_network": "hr_net"}
        self.assertRaises(exception.PciDeviceInvalidDeviceName,
                          devspec.PciDeviceSpec, pci_info)

    @mock.patch('zun.pci.utils.get_function_by_ifname',
                return_value=("0000:0a:00.0", True))
    def test_by_name(self, mock_get_function_by_ifname):
        pci_info = {"devname": "eth0", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertTrue(pci.match(dev))

    @mock.patch('zun.pci.utils.get_function_by_ifname',
                return_value=(None, False))
    def test_invalid_name(self, mock_get_function_by_ifname):
        pci_info = {"devname": "lo", "physical_network": "hr_net"}
        pci = devspec.PciDeviceSpec(pci_info)
        self.assertFalse(pci.match(dev))
