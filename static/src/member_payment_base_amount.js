/** @odoo-module **/

import { registry } from '@web/core/registry';
import { FormController } from '@web/views/form/form_controller';

const { Component, onMounted } = owl;

class CustomBaseAmountUpdater extends FormController {
    setup() {
        super.setup();
        onMounted(this._updateBaseAmount.bind(this));
    }

    // Function to calculate and set base_amount
   async _updateBaseAmount() {
    const paymentStructureLines = this.model.root.data.payment_structure_ids;
    if (paymentStructureLines && paymentStructureLines.length) {
        const records = await this.model.loadMany(paymentStructureLines);
        let total = 0;
        for (const record of records) {
            total += record.data.total_with_extra_amount || 0;
        }
        console.log('Computed base_amount total:', total); // Debug line
        await this.model.root.update({ base_amount: total });
    }
    } // <-- Ens


}

// Register the widget to apply to the form view
registry.category("controllers").add("member_payment_form_controller", CustomBaseAmountUpdater);
