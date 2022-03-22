export class Cart{
    total!: number
    tax!: number
    items!: Array<{"qty":number,"sku":string,"name":string,"price":number,"subtotal":number}> 
}