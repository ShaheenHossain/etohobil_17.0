odoo.define('etohobil.sync_amount', [
    'web.FormController', // Dependency for FormController
    'web.rpc' // Dependency for RPC calls
], function (require) {
    "use strict";

    const FormController = require('web.FormController');
    const rpc = require('web.rpc');

    const CustomFormController = FormController.include({
        async _onFieldChanged(event) {
            // Call the original method to retain default functionality
            await this._super(...arguments);

            // Check if the changed field is `member_transaction_ids`
            const changedField = event.data.changes ? Object.keys(event.data.changes)[0] : null;
            if (changedField === 'member_transaction_ids') {
                // Fetch the record ID
                const recordId = this.model.get(this.handle).data.id;
                if (recordId) {
                    try {
                        // Call the server method to compute the updated amount
                        const currentBaseAmount = await rpc.query({
                            model: 'account.move',
                            method: 'compute_base_amount_sync',
                            args: [recordId],
                        });

                        // Update the `current_base_amount` field in the view
                        this.model.updateFieldValue(
                            this.handle,
                            'current_base_amount',
                            currentBaseAmount
                        );
                    } catch (error) {
                        console.error('Failed to fetch current_base_amount:', error);
                    }
                }
            }
        },
    });

    return CustomFormController;
});
